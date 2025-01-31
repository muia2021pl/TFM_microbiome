!pip install scikit-bio

!pip install import-ipynb

import pandas as pd
import seaborn as sns
import numpy as np
import re
import matplotlib.pyplot as plt
import scipy.spatial.distance as ssd
import csv
from featurewiz import featurewiz

from sklearn.linear_model import ElasticNetCV, ElasticNet, LogisticRegression, LogisticRegressionCV, Lasso, LassoCV
from sklearn.model_selection import train_test_split, GridSearchCV, train_test_split, cross_val_score, RepeatedKFold
from sklearn.svm import LinearSVC
from sklearn.feature_selection import SelectFromModel, VarianceThreshold, SelectKBest, chi2, GenericUnivariateSelect, f_classif, mutual_info_classif
from sklearn import preprocessing
from sklearn.neighbors import KNeighborsClassifier, RadiusNeighborsClassifier 
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, Normalizer, MinMaxScaler
from sklearn import svm
from numpy import mean, std, absolute,arange
from pandas import read_csv
import sklearn.metrics as metrics
from sklearn.metrics import roc_auc_score,plot_roc_curve,roc_auc_score,roc_curve, confusion_matrix, cohen_kappa_score,ConfusionMatrixDisplay, make_scorer, f1_score, accuracy_score, r2_score, roc_curve, classification_report
#from skbio.stats.composition import clr
#from pyrolite.util.synthetic import normal_frame, random_cov_matrix
#import pyrolite.comp

import os
from google.colab import drive
drive.mount('/content/gdrive', force_remount=True)
from google.colab import files

os.chdir("/content/gdrive/My Drive/Colab Notebooks/")

import import_ipynb
import Microbiome_featureselection

"""**1. Read data from files (csv/tsv):**
1. metadata, 
2. metabolomics (mtb)
3. metagenomics (mgx) 
4. metatranscriptomics (mtx)
5. Selected participants IDs (3omics + 4tps)

Files where downloaded from: https://ibdmdb.org/tunnel/public/summary.html
"""

pd.options.display.max_colwidth = 250

# 1. metadata
metadata = pd.read_csv('hmp2_metadata_3omics4tp_curated.csv', sep= ';')
externalID_participant = metadata[["External ID"]]
externalID_participant = externalID_participant.set_index('External ID')

# 2. metabolomics
mtb = pd.read_csv('Metabolomics/hmp2_metabolomics_may21.csv', sep = ';')

# 3. metatranscriptomics. Se leen los dos archivos, el hmp2 y hmp2 pilot
mtx = pd.read_table('Metatranscriptomes/pathabundance_relab.tsv', index_col=0).transpose()
mtx_p = pd.read_table('Metatranscriptomes/pathabundances_mtx_pilot.tsv', index_col=0)


# 4. metagenomics
mgx = pd.read_table('Metagenomes/taxonomic_profiles.tsv', float_precision = "high")

# Preparamos el diccionario
subjects = pd.read_csv("participantID.csv", sep= ';')
abclist = subjects.loc[:, "A"]
numlist = subjects.loc[:, "B"]

"""**Preprocesamos el archivo metadata**



1.   hacemos que el indice del dataframe sea la columna "External ID"
2. añadimos un identificador a las columnas para saber que los datos son de tipo = clinico
3. Nos quedamos solo con las columnas de interes.


"""

# Procesado de archivo metadata
metadata = metadata[['External ID','Participant ID', 'site_sub_coll', 'data_type', 'week_num', 'diagnosis', 'Antibiotics']]
keep_same = {'External ID'}
metadata.columns = ['{}{}'.format(c, '' if c in keep_same else '$c') for c in metadata.columns]


# Imprimir el listado de columnas. 
list(metadata.columns.values)
#recordenar columnas
metadata = metadata[['External ID','Participant ID$c','diagnosis$c', 'site_sub_coll$c', 'data_type$c', 'week_num$c', 'Antibiotics$c']]

#Extraer metadata para type: metagenomics (1471 rows × 8 columns)
metadata_mgx = metadata.loc[metadata['data_type$c'] == 'metagenomics']
externalID_mgx = metadata_mgx[["External ID"]]
externalID_mgx = externalID_mgx.set_index('External ID')
metadata_mgx = metadata_mgx.set_index('External ID')

#Extraer metadata para type: metatranscriptomics (777 rows × 8 columns)
metadata_mtx = metadata.loc[metadata['data_type$c'] == 'metatranscriptomics']
externalID_mtx = metadata_mtx[["External ID"]]
externalID_mtx = externalID_mtx.set_index('External ID')
metadata_mtx = metadata_mtx.set_index('External ID')

#Extraer metadata para type: metabolomics (502 rows × 8 columns)
metadata_mtb = metadata.loc[metadata['data_type$c'] == 'metabolomics']
externalID_mtb = metadata_mtb[["External ID"]]
externalID_mtb = externalID_mtb.set_index('External ID')
metadata_mtb = metadata_mtb.set_index('External ID')

metadata_mtx

"""**Preprocesamos el archivo metabolomics:**

1.   mantenemos solo columnas clave de interes
2.   eliminamos todas las filas que no tienen metabolito identificado
3. Hacemos que la columna External ID sea la columna índice 
4. añadimos un identificador para saber que los datos pertenecen al tipo = metabolito.
5. Eliminamos los External ID de los participantes no incluidos en el estudio

Tras el procesado, el archivo tiene 492 rows × 657 columns, donde las filas son los IDs y las columnas son los metabolitos.
Tras eliminar las columnas duplicadas, el dataframe tiene 492 rows × 609 columns.
"""

# preprocesado del archivo metabolomics.
# 1. mantener solo columnas clave
mtb.drop(['Method','Pooled QC sample CV', 'm/z', 'RT', 'HMDB (*Representative ID)', 'Compound'], 1, inplace=True)

# 2. eliminar todas las filas que no tienen metabolito identificado. 
mtb = mtb[mtb['Metabolite'].notna()]
# 3. Hacer que Metabolito sea la columna índice
mtb = mtb.set_index('Metabolite').T

#4. Añadimos un identificador para saber que los datos pertenecen a tipo = metabolito
#mtb = mtb.add_suffix('mtb_')
keep_same = {'Metabolite'}
mtb.columns = ['{}{}'.format(c, '' if c in keep_same else '$mb') for c in mtb.columns]
mtb = mtb.add_prefix('m__')

# 5. Eliminamos external ID participantes excluidos del estudio
idx = externalID_participant.index.intersection(mtb.index)
mtb = mtb.loc[idx]

#Normalize data using log-ratios
#mtb = TFM_featureselection.fill_NA(mtb)
mtb = np.log10(mtb + 1)
# remove duplicate column names Ej: taurohyodeoxycholate/tauroursodeoxycholate
mtb = mtb.loc[:,~mtb.columns.duplicated()]
mtb= mtb.fillna(0)
mtb

"""**Preprocesamos el archivo metagenomics**
 
1. Seleccionar unicamente nivel taxonomico = Species
2. añadimos un identificador a las columnas para saber que los datos son de tipo = metagenomico
3. Eliminar filas que se correspondan con los sujetos no cualificados 

Una vez procesado el dataframe tiene 1448 rows × 492 columns. 


"""

# 1. Seleccionamos solo el nivel taxonomico = Species
# seleccionar las filas que tienen s__
mgx = mgx[mgx['#SampleID'].str.contains("s__")]

#eliminar las filas que tienen t__
mgx = mgx[~mgx['#SampleID'].str.contains('t__')]

#eliminar las filas que tienen tipo unclassified
mgx = mgx[~mgx['#SampleID'].str.contains('_unclassified')]


mgx['species'] = mgx['#SampleID'].str.split('s__').str[1]
mgx = mgx.set_index('species')
mgx = mgx.drop(columns = '#SampleID')
mgx = mgx.T

# 2. Añadimos identificador para tipo de dato OMICO 
keep_same = {'species'}
mgx.columns = ['{}{}'.format(c, '' if c in keep_same else '$tx') for c in mgx.columns]
mgx = mgx.add_prefix('s__')

# 3. Eliminamos external ID participantes excluidos del estudio
idx = externalID_participant.index.intersection(mgx.index)
mgx = mgx.loc[idx]

#Normalize data using log-ratios
mgx = mgx.fillna(0)
#mgx = TFM_featureselection.fill_NA(mgx)
lr_mgx = np.log10(mgx + 1)
#mgx = normalize(lr_mgx)
mgx = lr_mgx.fillna(0)

mgx

"""**Preprocesamos el archivo metatranscriptomics**



1. Añadimos sufijo _P a la tabla de MTX piloto
2. Eliminamos columnas que se corraspondan con los sujetos no cualificados
3. Transpose  
4. Comparar las columnas de las dos tablas MTX y MTX_p para ver si los pathways son comunes. O si son totalmente diferentes
5. hacemos que el indice del dataframe sea la columna "External ID"
6. añadimos un identificador a las columnas para saber que los datos son de tipo = metatranscriptomica

Una vez procesado, el dataframe tiene 749 rows × 6196 columns. (MTX filas = 680 y MTX_pilot filas = 69). 
"""

# 1. Añadimos el sufijo _P a los External ID para diferenciar los IDs que son del MTX piloto
keep_same = {'# Pathway'}
mtx_p.columns = ['{}{}'.format(c, '' if c in keep_same else '_P') for c in mtx_p.columns]
mtx_p = mtx_p.T


# Los Pathways que tienen en comun los dos ficheros (n=2687)
# a = mtx_p.columns.intersection(mtx.columns)

# 2. Añadimos el sufijo _pwy para diferenciar el tipo de dato: pathway transpritomics
keep_same = {'# Pathway'}
mtx.columns = ['{}{}'.format(c, '' if c in keep_same else '$pwy') for c in mtx.columns]

keep_same = {'#pathway_or_genefamily'}
mtx_p.columns = ['{}{}'.format(c, '' if c in keep_same else '$pwy') for c in mtx_p.columns]

# comprobar que sujetos no estan en nuestro metadata
# para fichero mtx
dif = externalID_mtx.index.difference(mtx.index)
dif

# para fichero mtx pilot
difp = externalID_mtx.index.difference(mtx_p.index)
difp

# 3. Eliminamos columnas de los sujetos no cualificados.
idx = externalID_mtx.index.intersection(mtx.index)
mtx = mtx.loc[idx]

idx2 = externalID_mtx.index.intersection(mtx_p.index)
mtx_p = mtx_p.loc[idx2]

#comprobamos cuantas columnas tienen diferentes. En total hay 2687 columnas (pathways iguales) y 3374 pathways unicos en cada set. 
#mtx.where(mtx.values==mtx_p.values).notna()
mtx_cols = mtx.columns
mtx_p_cols = mtx_p.columns

common_cols = mtx_cols.intersection(mtx_p_cols)
mtx_not_mtxp = mtx_cols.difference(mtx_p_cols)

# Unificamos las dos tablas de datos de transcriptomica: 
mtx_combined = mtx.append(mtx_p, sort=False)
mtx_combined = mtx_combined.add_prefix('g__')

# EJECTURAR SI QUEREMOS NORMALIZAR LOS DATOS
#mtx_combined = TFM_featureselection.fill_NA(mtx_combined)
lr_mtx = np.log10(mtx_combined + 1)
mtx = lr_mtx.fillna(0)

mtx = mtx.fillna(0)

mtx

"""**Spline Interpolation**

Varias opciones:
1. scipy.interpolate.splev()
Evaluate a B-spline or its derivatives. Given the knots and coefficients of a B-spline representation, evaluate the value of the smoothing polynomial and its derivatives. 

2. class scipy.interpolate.BSpline()
Univariate spline in the B-spline basis.

3. class scipy.interpolate.CubicSpline()
Cubic spline data interpolator.
Interpolate data with a piecewise cubic polynomial which is twice continuously differentiable. The result is represented as a PPoly instance with breakpoints matching the given data.
"""

#### POR COMPLETAR ###

"""**Feature Selection**

1. Low Variance
2. Univariate: ANOVA, Chi-squared, Mutual Information

1. Metatranscriptomic Data
"""

# 1. METATRANSCRIPTOMICS
MTX = pd.merge(metadata_mtx, mtx, left_index=True, right_index =True, sort=False, how='outer')
# CAMBIAR UC CD Y NONIBD POR NUMEROS
MTX = Microbiome_featureselection.pheno_to_numerical(MTX)
# prepare input (RNA abundances) and output (diagnosis) data 
MTX_X = MTX.iloc[:,7:len(MTX.columns)]
MTX_y = MTX.iloc[:,2]
MTX_X = Microbiome_featureselection.fill_NA(MTX_X)
# FEATURE SELECTION: Removing features with low variance
FS_MTX = Microbiome_featureselection.variance_threshold_selector(MTX_X)
# SPLIT TRAIN AND TEST DATASET
#X_train, X_test, y_train, y_test = train_test_split(FS_MTX, MTX_y, stratify=MTX_y, test_size=0.33)
X_train, X_test, y_train, y_test = train_test_split(FS_MTX, MTX_y, stratify=MTX_y, test_size=0.20)

#FEATURE IMPORTANCE
result, index, forest = Microbiome_featureselection.feature_importance(X_train, y_train, X_test) 

forest.feature_importances_
feature_names = X_train.columns

sorted_idx = forest.feature_importances_.argsort()
#sorted_idx_top = sorted_idx[1:10,]
sorted_idx_top = sorted_idx[5906:5916, ]
plt.barh(feature_names[sorted_idx_top], forest.feature_importances_[sorted_idx_top])
plt.xlabel("Random Forest Feature Importance")

#plt.barh(feature_names, forest.feature_importances_)

preds = forest.predict(X_test)
accuracy_score(preds, y_test)

#select top 50 features in original dataset
col = feature_names[sorted_idx[5866:5916, ]]
#mtx_filtered = Microbiome_featureselection.get_fs_columns_II (col, MTX)
mtx_filtered = Microbiome_featureselection.get_fs_columns_II(col, MTX)

mtx_filtered

# Feature selection Performance
#y_pred = TFM_featureselection.pipeline_ANOVA(X_train, y_train, X_test)
#y_pred = TFM_featureselection.pipeline_CHI2(X_train, y_train, X_test)
#y_pred = TFM_featureselection.pipeline_MI(X_train, y_train, X_test)
#print(classification_report(y_test, y_pred))

# Feature Selection for data Output
#mtx_top_chi2, mtx_test = Microbiome_featureselection.topfeatures_chi2(X_train, y_train, X_test)
#mtx_top_anova = TFM_featureselection.topfeatures_univariate(X_train, y_train)

# Nos quedamos con las 50 columnas seleccionadas del dataset original
#mtx_filtered = Microbiome_featureselection.get_fs_columns(mtx_top_chi2, mtx)

"""2. Metagenomic Data"""

# 2. METAGENOMICS
MGX = pd.merge(metadata_mgx, mgx, left_index=True, right_index =True, sort=False, how='outer')
# CAMBIAR UC CD Y NONIBD POR NUMEROS
MGX = Microbiome_featureselection.pheno_to_numerical(MGX)
# prepare input (RNA abundances) and output (diagnosis) data 
MGX_X = MGX.iloc[:,7:len(MGX.columns)]
MGX_y = MGX.iloc[:,2]
MGX_X = Microbiome_featureselection.fill_NA(MGX_X)
# FEATURE SELECTION: Removing features with low variance
FS_MGX = Microbiome_featureselection.variance_threshold_selector(MGX_X)
# SPLIT TRAIN AND TEST DATASET
X_train, X_test, y_train, y_test = train_test_split(FS_MGX, MGX_y, stratify=MGX_y, test_size=0.20)

#FEATURE IMPORTANCE
result, index, forest = Microbiome_featureselection.feature_importance(X_train, y_train, X_test) 

forest.feature_importances_
feature_names = X_train.columns

#SelectFromModel() will select those features which importance is greater than the mean importance of all the features by default,
sel = SelectFromModel(forest)
sel.fit(X_train, y_train)
sel.get_support()


selected_feat= X_train.columns[(sel.get_support())]
len(selected_feat)

print(selected_feat)

pd.Series(sel.estimator_.feature_importances_.ravel()).hist()

sorted_idx = forest.feature_importances_.argsort()
sorted_idx_top = sorted_idx[467:477,]
plt.barh(feature_names[sorted_idx_top], forest.feature_importances_[sorted_idx_top])
plt.xlabel("Random Forest Feature Importance")

preds = forest.predict(X_test)
accuracy_score(preds, y_test)

#select top 50 features in original dataset
col = feature_names[sorted_idx[427:477, ]]
mgx_filtered = Microbiome_featureselection.get_fs_columns_II (col, mgx)

mgx_filtered

# Feature selection Performance
#y_pred = TFM_featureselection.pipeline_ANOVA(X_train, y_train, X_test)
#y_pred = TFM_featureselection.pipeline_CHI2(X_train, y_train, X_test)
#y_pred = TFM_featureselection.pipeline_MI(X_train, y_train, X_test)
#print(classification_report(y_test, y_pred))

# Feature Selection for Output
#mgx_top_chi2, mgx_test = TFM_featureselection.topfeatures_chi2(X_train, y_train, X_test)
#mgx_top_anova = TFM_featureselection.topfeatures_univariate(X_train, y_train)

# Nos quedamos con las 200 columnas seleccionadas del dataset original
#mgx_filtered = TFM_featureselection.get_fs_columns(mgx_top_chi2, mgx)

"""3. Metabolomic Data"""

# 3. METABOLOMICS
MTB = pd.merge(metadata_mtb, mtb, left_index=True, right_index =True, sort=False, how='outer')
MTB = Mircrobiome_featureselection.pheno_to_numerical(MTB)
# prepare input (RNA abundances) and output (diagnosis) data 
MTB_X = MTB.iloc[:,7:len(MTB.columns)]
MTB_y = MTB.iloc[:,2]
#fill NA's
MTB = Microbiome_featureselection.fill_NA(MTB_X)
# FEATURE SELECTION: Removing features with low variance
FS_MTB = Microbiome_featureselection.variance_threshold_selector(MTB_X)
# SPLIT TRAIN AND TEST DATASET
X_train, X_test, y_train, y_test = train_test_split(FS_MTB, MTB_y, stratify=MTB_y, test_size=0.20)

#FEATURE IMPORTANCE
result, index, forest = Microbiome_featureselection.feature_importance(X_train, y_train, X_test) 

forest.feature_importances_
feature_names = X_train.columns

sorted_idx = forest.feature_importances_.argsort()
sorted_idx = forest.feature_importances_.argsort()
sorted_idx_top = sorted_idx[599:609,]
plt.barh(feature_names[sorted_idx_top], forest.feature_importances_[sorted_idx_top])
plt.xlabel("Random Forest Feature Importance")

preds = forest.predict(X_test)
accuracy_score(preds, y_test)

#select top 50 features in original dataset
col = feature_names[sorted_idx[559:609, ]]
mtb_filtered = Microbiome_featureselection.get_fs_columns_II (col, mtb)

mtb_filtered

# Feature selection Performance
#y_pred = TFM_featureselection.pipeline_ANOVA(X_train, y_train, X_test)
#y_pred = TFM_featureselection.pipeline_CHI2(X_train, y_train, X_test)
#y_pred = TFM_featureselection.pipeline_MI(X_train, y_train, X_test)
#print(classification_report(y_test, y_pred))

# Feature Selection for Output
#Extract 50 best features by a chi-squared test
#mtb_top_chi2, mtb_test = TFM_featureselection.topfeatures_chi2(X_train, y_train, X_test)
#mtb_top_anova = TFM_featureselection.topfeatures_univariate(X_train, y_train, X_test)


# Nos quedamos con las 50 columnas seleccionadas del dataset original
#mtb_filtered = TFM_featureselection.get_fs_columns(mtb_top_chi2, mtb)

#IDEA: la función SelectKBest devuelve tambien el valor score y asi podemos hacer un Plot de las K variables mas relevantes

"""**Preparar final file**

Unimos los 4 datasets: metadata, metabolomics, metagenomics and metatranscriptomics en una sola tabla.

- normalization (o cada dataset por separado?)
- método de spline (opcional)

Guardamos el df resultado en un fichero csv/txt para posteriormente procesarlo.
"""

metadata.drop(['data_type$c', 'site_sub_coll$c'], 1, inplace=True)
metadata = metadata.drop_duplicates(subset='External ID')
metadata = metadata.set_index('External ID')

rA = pd.merge(metadata, mtb_filtered, left_index=True, right_index =True, sort=False, how='outer')
rB=pd.merge(rA, mgx_filtered, left_index=True, right_index =True, sort=False, how='outer' )
rf = pd.merge(rB, mtx_filtered, left_index=True, right_index =True, sort=False, how='outer')

#Orden: cl, taxa, pathway, metabol.
#rA = pd.merge(metadata, mgx_filtered, left_index=True, right_index =True, sort=False, how='outer')
#rB=pd.merge(rA, mtx_filtered, left_index=True, right_index =True, sort=False, how='outer' )
#rf = pd.merge(rB, mtb_filtered, left_index=True, right_index =True, sort=False, how='outer')

rf = rf.reset_index()
rf = rf.fillna(0)

#Quitamos la _P que hace referencia al dataset hmp2 pilot 
#rf = rf.loc[rf['Participant ID__c'] == 'C3001']
rf['index'] = rf['index'].str.replace('_P','')
rf = rf.fillna(0)
rf.head()

#Al quitar el subindice de '_P', tenemos que agrupar las filas con el 'index' duplicado. 
rf = rf.groupby(['index', 'week_num$c']).first().reset_index()
#rf = rf.groupby('index')
rf

# Hay que ordenar el dataframe para que las week number de cada sujeto este en orden ascendente.
rf = rf.sort_values(by=['Participant ID$c', 'week_num$c'])
rf

# CAMBIAR UC CD Y NONIBD POR NUMEROS
# CD = 1, UC = 2, NON IBD = 3
rf = rf.replace({'CD': 1, 'UC': 2, 'nonIBD':3}) 

#Cambiar antibiotico
rf = rf.replace({'Yes': 1, 'No': 0})

#Cambiar los IDs de los participantes
my_dict = dict(zip(abclist, numlist))
#rf = rf.replace({"Participant ID__c": my_dict})
rf["Participant ID$c"] = rf["Participant ID$c"].map(my_dict)
rf = rf.fillna(0)

pid = rf['Participant ID$c']
rf.drop(labels=['Participant ID$c'], axis=1,inplace = True)
rf.insert(0, 'Participant ID$c', pid)

rf

# WRITE FILE 1: con index
#Guardamos el dataframe completo
#rf.to_csv('output_50best_normreduced_withindex.csv', encoding='utf-8', index=False)
rf.to_csv('output_50best_normreduced_withindex_2022.csv', encoding='utf-8', index=False)

rf_mean1 = rf.mean()
rf_mean = pd.DataFrame(rf_mean1).transpose()
rf_mean = rf_mean.stack().replace(',','.').unstack()
#rf_mean.to_csv('meanAbundanceTFM.txt', encoding='utf-8', index=True)
rf_mean

rf = rf.drop(['index'], axis=1)
rf = rf.drop(['Antibiotics$c'], axis=1)
#Write a separate file for each diagnosis
rfCD = rf.loc[rf['diagnosis$c'] == 1]
rfCD = rfCD.fillna(0)
rfCD = rfCD.drop(['diagnosis$c'], axis=1)
#rfCD.to_csv('output_CD_50.csv', encoding='utf-8', index=False)
rfCD.to_csv('output_CD_50_2022.csv', encoding='utf-8', index=False)

rfUC = rf.loc[rf['diagnosis$c'] == 2]
rfUC = rfUC.fillna(0)
rfUC = rfUC.drop(['diagnosis$c'], axis=1)
#rfUC.to_csv('output_UC_50.csv', encoding='utf-8', index=False)
rfUC.to_csv('output_UC_50_2022.csv', encoding='utf-8', index=False)

rfnonIBD = rf.loc[rf['diagnosis$c'] == 3]
rfnonIBD = rfnonIBD.fillna(0)
rfnonIBD = rfnonIBD.drop(['diagnosis$c'], axis=1)
#rfnonIBD.to_csv('output_nonIBD_50.csv', encoding='utf-8', index=False)
rfnonIBD.to_csv('output_nonIBD_50_2022.csv', encoding='utf-8', index=False)

rf

rf = rf.drop(['Participant ID$c'], axis=1)
rf = rf.drop(['week_num$c'], axis=1)
rf = rf.drop(['diagnosis$c'], axis=1)

rf

#rf = rf.drop(['index'], axis=1)

# WRITE FILE 2: sin index
#rf = rf.drop(['index'], axis=1)
#rf.to_csv('output_completo_normreduced_50.csv', encoding='utf-8', index=False)
rf.to_csv('output_completo_normreduced_50_2022.csv', encoding='utf-8', index=False)

rf

# WRITE FILE 2: sin index
#rf = rf.drop(['index'], axis=1)
rf.to_csv('output_completo_normreduced_50.csv', encoding='utf-8', index=False)

#GUARDAMOS UN SOLO SUJETO PARA QUE SEA MAS MANEJABLE
#rf = rf.loc[rf['Participant ID$c'] == 1]
#rf = rf.fillna(0)
#rf.to_csv('output_C3001_formatlab_normreduced_50.csv', encoding='utf-8', index=False)

rf

"""**RANDOM FOREST CLASSIFICATION**"""

# Prepare input and output data
rf_X = rf.iloc[:,5:len(rf.columns)]
rf_y = rf.iloc[:,3]

# Split train and test datasets
X_train, X_test, y_train, y_test = train_test_split(rf_X, rf_y, stratify=rf_y, test_size=0.33)


cm_RF, RF_clf, y_prob = Microbiome_featureselection.random_forest_clf(X_train, y_train, X_test, y_test)
sns.heatmap(cm_RF/np.sum(cm_RF), fmt='.2%' ,cmap="YlGnBu", annot=True)

cm_RF

macro_roc_auc_ovo = roc_auc_score(y_test, y_prob, multi_class="ovo",
                                  average="macro")
weighted_roc_auc_ovo = roc_auc_score(y_test, y_prob, multi_class="ovo",
                                     average="weighted")
macro_roc_auc_ovr = roc_auc_score(y_test, y_prob, multi_class="ovr",
                                  average="macro")
weighted_roc_auc_ovr = roc_auc_score(y_test, y_prob, multi_class="ovr",
                                     average="weighted")
print("One-vs-One ROC AUC scores:\n{:.6f} (macro),\n{:.6f} "
      "(weighted by prevalence)"
      .format(macro_roc_auc_ovo, weighted_roc_auc_ovo))
print("One-vs-Rest ROC AUC scores:\n{:.6f} (macro),\n{:.6f} "
      "(weighted by prevalence)"
      .format(macro_roc_auc_ovr, weighted_roc_auc_ovr))


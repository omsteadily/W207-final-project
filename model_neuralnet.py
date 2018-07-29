
# coding: utf-8

# # Neural Network Notebook
# [Return to project overview](final_project_overview.ipynb)
# 
# 
# ### Andrew Larimer, Deepak Nagaraj, Daniel Olmstead, Michael Winton (W207-4-Summer 2018 Final Project)

# In[1]:


# import necessary libraries
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import util

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

# set default options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 200)

get_ipython().magic('matplotlib inline')


# ## Load data and split class labels into separate array
# 
# Our utility function reads the merged dataset, imputes the column mean for missing numeric values, and then performs a stratified train-test split.

# In[2]:


train_data, test_data, train_labels, test_labels = util.read_data()
print(train_data.shape)
print(train_labels.shape)


# > **KEY OBSERVATION**: a hypothetical model that is hard-coded to predict a `negative` result every time would be ~77% accurate.  So, we should not accept any machine-learned model with a lower accuracy than that.  This also suggests that F1 score is a better metric to assess our work since it incorporates both precision and recall.

# In[3]:


train_data.info()
train_data.head(10)


# > **KEY OBSERVATION**: the feature `school_income_estimate` only has non-null values for 104 of 371 records in the training data.  We should drop it from further analysis, as imputing its value for the non-null records isn't appropriate.

# ## Create a function to estimate MLP models and report results

# In[4]:


def estimate_mlp(train_data, train_labels, k_folds=10, max_iter=1000):
    # create a pipeline to run StandardScaler and MLP
    n_features = train_data.shape[1]
    pipe_clf = make_pipeline(StandardScaler(with_mean=False), 
                       MLPClassifier(hidden_layer_sizes=(n_features,n_features,n_features), max_iter=max_iter))

    # Do k-fold cross-validation, collecting both "test" accuracy and F1 
    print('Running cross-validation, please be patient...')
    cv_scores = cross_validate(pipe_clf, train_data, train_labels, cv=k_folds, scoring=['accuracy','f1'])
    util.print_cv_results(cv_scores)


# ## Train and fit a "naive" model
# For the first model, we'll use all features except SHSAT-related features because they are too correlated with the way we calculated the label.  We'll also drop `school_income_estimate` because it's missing for ~2/3 of the schools.

# In[5]:


drop_cols = ['dbn',
             'num_shsat_test_takers',
             'offers_per_student',
             'pct_test_takers',
             'school_name',
             'school_income_estimate',
            ]

# drop SHSAT-related columns
train_data_naive = train_data.drop(drop_cols, axis=1)
test_data_naive = test_data.drop(drop_cols, axis=1)

print(train_data_naive.shape)
train_data_naive.head()


# ## One Hot Encode the categorical explanatory variables
# Columns such as zip code and school district ID, which are integeres should not be fed into an ML model as integers.  Instead, we would need to treat them as factors and perform one-hot encoding.  

# In[6]:


train_data_naive_ohe, test_data_naive_ohe = util.ohe_data(train_data_naive, test_data_naive)


# ## Estimate the "naive" multilayer perceptron model
# This first "naive" model uses all except for the SHSAT-related features, as described above.  We create a pipeline that will be used for k-fold cross-validation.  First, we scale the features, then estimate a multilayer perceptron neural network.

# In[7]:


estimate_mlp(train_data_naive_ohe, train_labels, k_folds=10, max_iter=1000)


# ## Train a "naive" model without zip code or school district
# Next, we will remove the zip and district features and compare accuracy to the model that included one hot-encoded versions of these factors.

# In[8]:


drop_cols = ['dbn',
             'num_shsat_test_takers',
             'offers_per_student',
             'pct_test_takers',
             'school_name',
             'school_income_estimate',
             'district',
             'zip',
            ]

# drop SHSAT-related columns + district, zip
train_data_naive_nozip = train_data.drop(drop_cols, axis=1)
test_data_naive_nozip = test_data.drop(drop_cols, axis=1)

print(train_data_naive_nozip.shape)
print(train_labels.shape)
train_data_naive_nozip.head()


# ## Estimate the "naive" multilayer perceptron model (without zip or district)
# 

# In[9]:


estimate_mlp(train_data_naive_nozip, train_labels, k_folds=10, max_iter=1000)


# > **KEY OBSERVATION**: while the accuracy is similar when we exclude zip code and school district, the F1 score is substantially less, with a 95% confidence interval that nearly spans the interval 0-1.  This suggests that it's important to keep these factors in the model. 

# ## Train a "race-blind" multilayer perceptron model
# Because we know there's an existing bias problem in the NYC schools, in that the demographics of the test taking population have been getting more homogenous, and the explicit goal of PASSNYC is to make the pool more diverse, we want to train a model that excludes most demographic features.  This would enable us to train a "race-blind" model.  
# 
# ### Preprocess new X_train and X_test datasets
# We will remove all explicitly demographic columns, as well as economic factors and zip code, which are likely highly correlated with demographics.

# In[11]:


# drop SHSAT-related columns
drop_cols = ['dbn',
             'num_shsat_test_takers',
             'offers_per_student',
             'pct_test_takers',
             'school_name',
             'school_income_estimate'
            ]
train_data_race_blind = train_data.drop(drop_cols, axis=1)
test_data_race_blind = test_data.drop(drop_cols, axis=1)

# drop additional (demographic) columns
race_cols = ['percent_ell',
             'percent_asian',
             'percent_black',
             'percent_hispanic',
             'percent_black__hispanic',
             'percent_white',
             'economic_need_index',
             'zip'
             ]
train_data_race_blind = train_data_race_blind.drop(race_cols, axis=1)
test_data_race_blind = test_data_race_blind.drop(race_cols, axis=1)

# one-hot encode these features as factors
factor_cols = ['district']
train_data_race_blind_ohe, test_data_race_blind_ohe = util.ohe_data(train_data_naive, test_data_naive, factor_cols)


# ## Estimate the "race blind" multilayer perceptron model
# 

# In[12]:


estimate_mlp(train_data_race_blind_ohe, train_labels, k_folds=10, max_iter=1000)


# > **KEY OBSERVATION**: the F1 score for the race-blind model also have a 95% confidence interval that nearly spans the whole range from 0-1.  Of the models we have tested, the original "naive" model (with the most features) performs better than our race-blind model, or our model that excluded only zip and district.

# ## Experiment with hidden layer parameters in the "naive" model
# Next, we will return to the feature set of the original "naive" model, but will explore different numbers of h

# ## Final test set accuracy

# In[ ]:


# y_predict = mlp.predict(X_test)

# print(confusion_matrix(y_test,y_predict))
# print(classification_report(y_test,y_predict))

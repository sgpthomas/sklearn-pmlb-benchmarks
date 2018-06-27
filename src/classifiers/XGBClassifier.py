import sys
import pandas as pd
import numpy as np
import itertools
from sklearn.preprocessing import RobustScaler
from xgboost import XGBClassifier # Assumes XGBoost v0.6
from classifiers.evaluate_model import evaluate_model

# dataset = sys.argv[1]
def get_pipeline_parameters():
    n_estimators_values = [10, 50, 100, 500]
    learning_rate_values = [0.01, 0.1, 1.0, 10.0, 100.0]
    # learning_rate_values = [0.01, 0.1, 0.5, 1.0, 10.0, 50.0, 100.0]
    gamma_values = np.arange(0., 0.51, 0.1)
    # gamma_values = np.arange(0., 0.51, 0.05)
    max_depth_values = [1, 2, 3, 4, 5, 10, 20, None]
    # max_depth_values = [1, 2, 3, 4, 5, 10, 20, 50, None]
    subsample_values = np.arange(0.0, 1.01, 0.2)
    # subsample_values = np.arange(0.0, 1.01, 0.1)
    random_state = [324089]

    all_param_combinations = itertools.product(n_estimators_values, learning_rate_values, gamma_values, max_depth_values, subsample_values, random_state)
    pipeline_parameters = \
        [{'n_estimators': n_estimators, 'learning_rate': learning_rate, 'gamma': gamma, 'max_depth': max_depth, 'subsample': subsample, 'seed': random_state, 'nthread': 1}
        for (n_estimators, learning_rate, gamma, max_depth, subsample, random_state) in all_param_combinations]
    return pipeline_parameters

def run(dataset, params, resultdir=".", use_params=True):
    pipeline_parameters = {}
    if use_params:
        pipeline_parameters[XGBClassifier] = params

    pipeline_components = [RobustScaler, XGBClassifier]
    return evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir=resultdir)

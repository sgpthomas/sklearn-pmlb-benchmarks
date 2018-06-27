import sys
import pandas as pd
import numpy as np
import itertools
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import AdaBoostClassifier
from classifiers.evaluate_model import evaluate_model

def get_pipeline_parameters():
    learning_rate_values = [0.01, 0.1, 0.5, 1.0, 10.0, 50.0, 100.0]
    n_estimators_values = [10, 50, 100, 500]
    random_state = [324089]

    all_param_combinations = itertools.product(learning_rate_values, n_estimators_values, random_state)
    pipeline_parameters = [{'learning_rate': learning_rate,
                            'n_estimators': n_estimators,
                            'random_state': random_state}
                           for (learning_rate, n_estimators, random_state) in all_param_combinations]
    return pipeline_parameters

def run(dataset, params, resultdir=".", use_params=True):
    pipeline_parameters = {}
    if use_params:
        pipeline_parameters[AdaBoostClassifier] = params

    pipeline_components = [RobustScaler, AdaBoostClassifier]
    return evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir=resultdir)

import sys
import pandas as pd
import numpy as np
import itertools
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import PassiveAggressiveClassifier
from classifiers.evaluate_model import evaluate_model

# dataset = sys.argv[1]
def get_pipeline_parameters():
    C_values = [0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1, 0.5, 1., 10., 50., 100.]
    loss_values = ['hinge', 'squared_hinge']
    fit_intercept_values = [True, False]
    random_state = [324089]

    all_param_combinations = itertools.product(C_values, loss_values, fit_intercept_values, random_state)
    pipeline_parameters = \
        [{'C': C, 'loss': loss, 'fit_intercept': fit_intercept, 'random_state': random_state}
        for (C, loss, fit_intercept, random_state) in all_param_combinations]
    return pipeline_parameters

def run(dataset, params, resultdir=".", use_params=True):
    pipeline_parameters = {}
    if use_params:
        pipeline_parameters[PassiveAggressiveClassifier] = params

    pipeline_components = [RobustScaler, PassiveAggressiveClassifier]
    return evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir=resultdir)

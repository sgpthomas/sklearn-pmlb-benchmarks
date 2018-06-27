import sys
import pandas as pd
import numpy as np
import itertools
from sklearn.preprocessing import RobustScaler
from sklearn.neighbors import KNeighborsClassifier
from classifiers.evaluate_model import evaluate_model

# dataset = sys.argv[1]
def get_pipeline_parameters():
    n_neighbors_values = list(range(1, 26)) + [50, 100]
    weights_values = ['uniform', 'distance']

    all_param_combinations = itertools.product(n_neighbors_values, weights_values)
    pipeline_parameters = \
        [{'n_neighbors': n_neighbors, 'weights': weights}
        for (n_neighbors, weights) in all_param_combinations]
    return pipeline_parameters

def run(dataset, params, resultdir=".", use_params=True):
    pipeline_parameters = {}
    if use_params:
        pipeline_parameters[KNeighborsClassifier] = params

    pipeline_components = [RobustScaler, KNeighborsClassifier]
    return evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir=resultdir)

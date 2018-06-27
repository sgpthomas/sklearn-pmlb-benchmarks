import sys
import pandas as pd
import numpy as np
import itertools
from sklearn.preprocessing import RobustScaler
from sklearn.naive_bayes import GaussianNB
from classifiers.evaluate_model import evaluate_model

# dataset = sys.argv[1]

def get_pipeline_parameters():
    pipeline_parameters = [{}]
    return pipeline_parameters

def run(dataset, params, resultdir=".", use_params=True):
    pipeline_parameters = {}
    if use_params:
        pipeline_parameters[GaussianNB] = params

    pipeline_components = [RobustScaler, GaussianNB]
    return evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir=resultdir)

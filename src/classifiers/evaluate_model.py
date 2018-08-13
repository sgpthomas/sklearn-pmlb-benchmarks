import sys
import itertools
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.metrics import make_scorer
from sklearn.pipeline import make_pipeline
from tpot_metrics import balanced_accuracy_score
import warnings
from pmlb import fetch_data
import os
from pathlib import Path

def map2_dict(f, d):
    '''takes a function f(key, value) -> (key, value)'''
    res = {}
    for k, v in d.items():
        tup = f(k, v)
        res[tup[0]] = tup[1]
    return res

def dict_safe_append(d, key, i):
    '''If key already exists, performs d[key].append(i), otherwise performs d[key] = [i]'''
    if key not in d:
        d[key] = [i]
    else:
        d[key].append(i)

def evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir="."):
    '''dataset: str, pipeline_components: List[Object], Dict[Object, Dict[str, Any]]'''

    # download dataset from PMLB
    input_data = fetch_data(dataset)

    # separate features and labels
    features = input_data.drop('target', axis=1).values.astype(float)
    labels = input_data['target'].values

    results_dict = {} # initialize a dictionary to store the results
    classifier_class = pipeline_components[-1] # the classifier is the last element on the components list

    with warnings.catch_warnings():
        # Squash warning messages. Turn this off when debugging!
        warnings.simplefilter('ignore')

        # initialize each of the components in the pipeline, passing in parameters if we have them
        pipeline = []
        for component in pipeline_components:
            if component in pipeline_parameters:
                args = pipeline_parameters[component]
                pipeline.append(component(**args))
            else:
                pipeline.append(component())

        try:
            clf = make_pipeline(*pipeline) # make the pipeline
            cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=90483257) # initialize the cross validiation
            # these are the metrics we are collecting
            scoring = {'accuracy': 'accuracy',
                        'f1_macro': 'f1_macro',
                        'bal_accuracy': make_scorer(balanced_accuracy_score)}
            validation = cross_validate(clf, features, labels, cv=cv, scoring=scoring) # perform the cross validiation
            avg = map2_dict(lambda k, v: ("avg_{}".format(k), np.mean(v)), validation) # save average of cross validiation
            stddev = map2_dict(lambda k, v: ("std_{}".format(k), np.std(v)), validation) # save std dev of cross valiiation
        except KeyboardInterrupt:
            sys.exit(1)
        # This is a catch-all to make sure that the evaluation won't crash due to a bad parameter
        # combination or bad data. Turn this off when debugging!
        except Exception as e:
            pass

        # construct parameter string
        param_string = "default"
        if pipeline_parameters != {}:
            param_string = ','.join(['{}={}'.format(parameter, value)
                                        for parameter, value in
                                        pipeline_parameters[classifier_class].items()])

        # add things to the results dictionary
        dict_safe_append(results_dict, 'dataset', dataset)
        dict_safe_append(results_dict, 'classifier', classifier_class.__name__)
        dict_safe_append(results_dict, 'parameters', param_string)

        # merge the avg and stddev dictionaries
        merged = {**avg, **stddev}

        # add everything to the results dictionary
        for key in merged:
            dict_safe_append(results_dict, key, merged[key])

        return results_dict

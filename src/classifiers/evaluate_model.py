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

def map_dict(f, d):
    return { k: f(v) for k, v in d.items() }

def map2_dict(f, d):
    res = {}
    for k, v in d.items():
        tup = f(k, v)
        res[tup[0]] = tup[1]
    return res

def merge_dicts(d1, d2):
    if d1 == {}:
        return d2
    if d1.keys() != d2.keys():
        raise Exception("Keys must match: {} != {}".format(d1.keys(), d2.keys()))
    for k in d1:
        d1[k] += d2[k]
    return d1

def dict_safe_append(d, key, i):
    if key not in d:
        d[key] = [i]
    else:
        d[key].append(i)

def evaluate_model(dataset, pipeline_components, pipeline_parameters, resultdir="."):
    input_data = fetch_data(dataset)
    features = input_data.drop('target', axis=1).values.astype(float)
    labels = input_data['target'].values

    # pipelines = [dict(zip(pipeline_parameters.keys(), list(parameter_combination)))
    #              for parameter_combination in itertools.product(*pipeline_parameters.values())]
    # pipelines = pipeline_parameters

    results_dict = {}
    classifier_class = pipeline_components[-1]
    # tmpfn = '{}/tmp--{}--{}.pkl'.format(resultdir, dataset, classifier_class.__name__)
    # Path(tmpfn).touch()
    with warnings.catch_warnings():
        # Squash warning messages. Turn this off when debugging!
        warnings.simplefilter('ignore')

        # for pipe_parameters in pipelines:
        pipeline = []
        for component in pipeline_components:
            # if component in pipe_parameters:
            if component in pipeline_parameters:
                args = pipeline_parameters[component]
                pipeline.append(component(**args))
            else:
                pipeline.append(component())

        try:

            clf = make_pipeline(*pipeline)
            cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=90483257)
            scoring = {'accuracy': 'accuracy',
                        'f1_macro': 'f1_macro',
                        'bal_accuracy': make_scorer(balanced_accuracy_score)}
            validation = cross_validate(clf, features, labels, cv=cv, scoring=scoring)
            avg = map2_dict(lambda k, v: ("avg_{}".format(k), np.mean(v)), validation)
            stddev = map2_dict(lambda k, v: ("std_{}".format(k), np.std(v)), validation)
            # balanced_accuracy = balanced_accuracy_score(labels, cv_predictions)
        except KeyboardInterrupt:
            sys.exit(1)
        # This is a catch-all to make sure that the evaluation won't crash due to a bad parameter
        # combination or bad data. Turn this off when debugging!
        # except Exception as e:
        #     continue

        param_string = "default"
        if pipeline_parameters != {}:
            param_string = ','.join(['{}={}'.format(parameter, value)
                                        for parameter, value in
                                        pipeline_parameters[classifier_class].items()])

        dict_safe_append(results_dict, 'dataset', dataset)
        dict_safe_append(results_dict, 'classifier', classifier_class.__name__)
        dict_safe_append(results_dict, 'parameters', param_string)
        merged = {**avg, **stddev}
        for key in merged:
            dict_safe_append(results_dict, key, merged[key])

        # out_text = '\t'.join(map_dict(lambda v: str(v[-1]), results_dict).values())
        # print(out_text, flush=True)

        # pd.DataFrame(results_dict).to_pickle(tmpfn)

        # os.remove(tmpfn)
        # final_fn = '{}/final--{}--{}.pkl'.format(resultdir, dataset, classifier_class.__name__)
        # pd.DataFrame(results_dict).to_pickle(final_fn)
        return results_dict

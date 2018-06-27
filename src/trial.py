#!/usr/bin/env python3

from pmlb import classification_dataset_names
import os
import sys
import glob
import itertools
import argparse
import multiprocessing
import traceback


def run(resultdir, dataset, method):
    if not isinstance(dataset, str):
        raise TypeError("Input must be a string!")

    classifier_functions[method](dataset, resultdir=resultdir, use_params=False)

def make_parser():
    dscr = "Script to run sklearn benchmarks on the PMLB datasets."
    parser = argparse.ArgumentParser(description=dscr)

    parser.add_argument('resultdir', action="store")
    parser.add_argument('-d', '--dataset', action="store_true")
    parser.add_argument('-c', '--count', action="store", default=1, type=int)
    parser.add_argument('-p', '--processes', action="store", default=1, type=int)

    return parser

if __name__ == "__main__":
    options = make_parser().parse_args()

    def iteration(todo, attempts=5):
        try:
            dataset, method = todo
            print(todo)
            run(options.resultdir, dataset, method)
        except Exception as err:
            if attempts < 0:
                traceback.print_exception(err)
                return None
            else:
                print("Tring {} again!".format(todo))
                iteration(todo, attempts=(attempts-1))

    if options.dataset:
        options.count *= len(classifier_functions.keys())

    if options.count > len(todos):
        options.count = len(todos)

    with multiprocessing.Pool(processes=options.processes) as pool:
        list(pool.map(iteration, todos[:options.count]))

    print("Done!")

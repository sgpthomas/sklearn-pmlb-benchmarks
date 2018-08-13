#!/usr/bin/env python3

import socket
import argparse
import trial_msg
import itertools
from pathlib import Path

import traceback
import os
import sys
import pandas as pd
from time import sleep
from multiprocessing import Process, Queue
import queue

from pmlb import classification_dataset_names

from classifiers import AdaBoostClassifier
from classifiers import BernoulliNB
from classifiers import DecisionTreeClassifier
from classifiers import ExtraTreesClassifier
from classifiers import GaussianNB
from classifiers import GradientBoostingClassifier
from classifiers import KNeighborsClassifier
from classifiers import LinearSVC
from classifiers import LogisticRegression
from classifiers import MultinomialNB
from classifiers import PassiveAggressiveClassifier
from classifiers import RandomForestClassifier
from classifiers import SGDClassifier
from classifiers import SVC
from classifiers import XGBClassifier

# globals
classifier_functions = {
    "AdaBoostClassifier": AdaBoostClassifier, # 28
    "BernoulliNB": BernoulliNB, # 140
    "DecisionTreeClassifier": DecisionTreeClassifier, # 280
    "ExtraTreesClassifier": ExtraTreesClassifier, # 1120
    "GaussianNB": GaussianNB, # 1
    "GradientBoostingClassifier": GradientBoostingClassifier, # 7840
    "KNeighborsClassifier": KNeighborsClassifier, # 54
    "LinearSVC": LinearSVC, # 320
    "LogisticRegression": LogisticRegression, # 240
    "MultinomialNB": MultinomialNB, # 20
    "PassiveAggressiveClassifier": PassiveAggressiveClassifier, # 44
    "RandomForestClassifier": RandomForestClassifier, # 1120
    "SGDClassifier": SGDClassifier, # 5000
    "SVC": SVC, # 1232
    "XGBClassifier": XGBClassifier # 30492
}

class Death(Exception):
    '''An exception because you can't break out of the outer loop from an inner loop in python.
    This exception is used when a client terminates or sends nonsense. '''
    pass


resultdir = "." # default result dir

def flatten(l):
    '''Takes a list of lists and returns a 1d list.
    e.g. flatten( [[1.], [2.], [3.]] ) -> [1., 2., 3.] '''
    return [item for sublist in l for item in sublist]

def make_parser():
    '''Construct the option parser'''
    descr = "Scheduler that hands out trials and collects results."
    parser = argparse.ArgumentParser(description=descr)

    parser.add_argument('resultdir', action="store")
    parser.add_argument('-p', '--port', action="store", default=3000, type=int)
    parser.add_argument('-m', '--max-connections', action="store", default=100, type=int)
    parser.add_argument('--default', action="store_true")
    parser.add_argument('--resume', action="store_true")

    return parser

def start_server(port):
    '''Start a server at the given port and return the socket object.'''
    s = socket.socket()
    host = socket.gethostname()
    s.bind((host, port))
    print("Started server at {}:{}".format(s.getsockname()[0], port))
    return s

def stop_server(server):
    '''Close the server'''
    server.close()

def send_msg(client, msg):
    '''Send the given client the given dictionary.'''
    client.send(trial_msg.serialize(msg))

def committer(commit_queue):
    '''Watches the given queue and attempts to commit dataframes
    in the queue to a file.'''
    while True:
        try:
            item = commit_queue.get()
            if item == None:
                print("Terminating committer!")
                break

            res, prefix, ident, remaining, percent = item
            pd.DataFrame(res).to_pickle("{}/{}-{}.pkl".format(resultdir, prefix, ident))
            print("[*] Commited #{} ({} remaining, {:.4%} completed)".format(ident, remaining, percent))
        except:
            traceback.print_exc()

MAX_TIMEOUT = 1000
def handler(pid, client, todo_queue, total):
    '''The backbone of the scheduler. Handles all communication between clients.'''
    hostname, port = client.getsockname()
    timeout = 0
    # owned_tasks = set()
    print("Started [{}] : {}".format(pid, hostname))
    client.settimeout(1)
    while True:
        try:
            if timeout > MAX_TIMEOUT:
                print("[{}] {} timed out!".format(pid, hostname))
                break

            # receive any data from the client
            data = trial_msg.deserialize(client.recv(trial_msg.SIZE))

            # if we receive nothing, kill this client
            if data == None:
                print("[{}] {} died! Removing!".format(pid, hostname))
                break

            # for every packet
            for data in data:
                timeout = 0
                msg_type = data['msg_type']
                # switch on msg_type
                if msg_type == trial_msg.VERIFY:
                    send_msg(client, {'msg_type': trial_msg.SUCCESS})

                elif msg_type == trial_msg.TRIAL_REQUEST:
                    # attempt to get a new trial to send to the client
                    ident, dataset, method, params = None, None, None, None
                    try:
                        ident, dataset, method, params = todo_queue.get(block=True, timeout=1)
                    except queue.Empty:
                        print("No more trials!")
                        send_msg(client, {'msg_type': trial_msg.TERMINATE})
                        break

                    # owned_tasks.add(ident)
                    msg = {'msg_type': trial_msg.TRIAL_DETAILS,
                           'id': ident,
                           'dataset': dataset,
                           'method': method,
                           'params': params}
                    send_msg(client, msg)
                    print("[*] -> [{}] : Handed out #{}: {} {} {}".format(pid, ident, dataset, method, list(params.values())))

                elif msg_type == trial_msg.TRIAL_DONE:
                    # client finished a trial, add result to commit queue
                    ident = data['id']
                    trial_result = data['data']
                    print("[*] <- [{}] : Finished #{}".format(pid, ident))

                    qsize = todo_queue.qsize()
                    commit_queue.put((trial_result, 'tmp', ident, qsize, 1. - (qsize / total)))

                    send_msg(client, {'msg_type': trial_msg.SUCCESS})
                    # owned_tasks.remove(ident)

                elif msg_type == trial_msg.TRIAL_CANCEL:
                    # client aborted trial, commit reason
                    ident = data['id']
                    reason = data['reason']
                    print("[*] <- [{}] : Aborted #{} b/c {}!".format(pid, ident, reason))

                    qsize = todo_queue.qsize()
                    trial_result = {
                        'id': [ident],
                        'reason': [reason]
                    }
                    commit_queue.put((trial_result, 'bad', ident, qsize, 1. - (qsize / total)))

                    send_msg(client, {'msg_type': trial_msg.SUCCESS})
                    # owned_tasks.remove(ident)

                elif msg_type == trial_msg.TERMINATE:
                    # client terminated, kill handler for this the client
                    print("[*] <- [{}] : Terminated!".format(pid))
                    raise Death

                else:
                    # got gibberish, kill handler for this client
                    print("[*] <- [{}] : Unknown msg type: {}".format(pid, msg_type))
                    raise Death

        except socket.timeout:
            timeout += 1
        except Death:
            break
        except Exception as e:
            print("Something broke on [{}] {}!".format(pid, hostname))
            traceback.print_exc()

    client.close()
    print("[*] Process {} died!".format(pid), flush=True)

if __name__ == "__main__":
    options = make_parser().parse_args() # get command line options

    # make results directory of it doesn't exist
    try:
        os.mkdir(options.resultdir)
    except OSError:
        pass

    resultdir = options.resultdir

    # gather todos
    print("Gathering todos...", end='', flush=True)
    todo_queue = Queue()
    completed = set()
    if options.resume:
        # read all ids from filenames in resultdir and add them to the completed set
        p = Path(resultdir)
        ids = list(map(lambda s: int(s.stem.split('-')[1]), p.glob("*.pkl")))
        for i in ids:
            completed.add(i)

    # get all parameter settings
    if options.default:
        params = {key: [{}] for key in classifier_functions}
    else:
        params = {key: item.get_pipeline_parameters()
                  for key, item in classifier_functions.items()}

    # add everything that is not completed to the todo queue
    ident = 0
    for name in classification_dataset_names:
        for key in sorted(params):
            for x in params[key]:
                if ident not in completed:
                    todo_queue.put((ident, name, key, x))
                ident += 1
    total = ident
    print("found {} incomplete trials!".format(todo_queue.qsize(), flush=True))

    # start the committer process
    commit_queue = Queue()
    committer_p = Process(target=committer, args=(commit_queue,))
    committer_p.start()

    # start the server and start listening for clients
    s = start_server(options.port)
    print("Starting to listen...", flush=True)
    s.listen(options.max_connections)

    processes = {}
    try:
        while True:
            # every time we find a new client, start a handler process for it
            c, addr = s.accept()
            p = Process(target=handler, args=(len(processes.keys()), c, todo_queue, total))
            p.start()
            processes[addr] = p
    except KeyboardInterrupt:
        print("Shutting down server!")

    # kill the committer process
    commit_queue.put(None)
    committer_p.join()

    # join all handler processes
    for p in processes.values():
        p.join()

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
from todo import TodoList

# s.listen(5)

# while True:
#     c, addr = s.accept()

#     print("Connected to {}".format(addr))
#     c.send(b"Hello!")
#     c.close()

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

class Death(Exception): pass

resultdir = "."

def flatten(l):
    return [item for sublist in l for item in sublist]

def make_parser():
    descr = "Scheduler that hands out trials and collects results."
    parser = argparse.ArgumentParser(description=descr)

    parser.add_argument('resultdir', action="store")
    parser.add_argument('-p', '--port', action="store", default=3000, type=int)
    parser.add_argument('-m', '--max-connections', action="store", default=100, type=int)
    parser.add_argument('--default', action="store_true")
    parser.add_argument('--resume', action="store_true")

    return parser

def start_server(port):
    s = socket.socket()
    host = socket.gethostname()
    s.bind((host, port))
    print("Started server at {}:{}".format(s.getsockname()[0], port))
    return s

def stop_server(server):
    server.close()

def send_msg(client, msg):
    client.send(trial_msg.serialize(msg))

def committer(commit_queue):
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
    hostname, port = client.getsockname()
    timeout = 0
    owned_tasks = set()
    print("Started [{}] : {}".format(pid, hostname))
    client.settimeout(1)
    while True:
        try:
            if timeout > MAX_TIMEOUT:
                print("[{}] {} timed out!".format(pid, hostname))
                break

            data = trial_msg.deserialize(client.recv(trial_msg.SIZE))

            if data == None:
                print("[{}] {} died! Removing!".format(pid, hostname))
                break

            for data in data:
                timeout = 0
                msg_type = data['msg_type']
                if msg_type == trial_msg.VERIFY:
                    send_msg(client, {'msg_type': trial_msg.SUCCESS})

                elif msg_type == trial_msg.TRIAL_REQUEST:
                    ident, dataset, method, params = None, None, None, None
                    try:
                        ident, dataset, method, params = todo_queue.get(True, 1)
                    except queue.Empty:
                        print("No more trials!")
                        send_msg(client, {'msg_type': trial_msg.TERMINATE})
                        break

                    owned_tasks.add(ident)
                    msg = {'msg_type': trial_msg.TRIAL_DETAILS,
                           'id': ident,
                           'dataset': dataset,
                           'method': method,
                           'params': params}
                    send_msg(client, msg)
                    print("[*] -> [{}] : Handed out #{}: {} {} {}".format(pid, ident, dataset, method, list(params.values())))

                elif msg_type == trial_msg.TRIAL_DONE:
                    ident = data['id']
                    trial_result = data['data']
                    print("[*] <- [{}] : Finished #{}".format(pid, ident))

                    qsize = todo_queue.qsize()
                    commit_queue.put((trial_result, 'tmp', ident, qsize, 1. - (qsize / total)))

                    send_msg(client, {'msg_type': trial_msg.SUCCESS})
                    owned_tasks.remove(ident)

                elif msg_type == trial_msg.TRIAL_CANCEL:
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
                    owned_tasks.remove(ident)

                elif msg_type == trial_msg.TERMINATE:
                    print("[*] <- [{}] : Terminated!".format(pid))
                    raise Death

                else:
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
    options = make_parser().parse_args()

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
        p = Path(resultdir)
        ids = list(map(lambda s: int(s.stem.split('-')[1]), p.glob("*.pkl")))
        for i in ids:
            completed.add(i)

    if options.default:
        params = {key: [{}] for key in classifier_functions}
    else:
        params = {key: item.get_pipeline_parameters()
                  for key, item in classifier_functions.items()}
    ident = 0
    for name in classification_dataset_names:
        for key in sorted(params):
            for x in params[key]:
                if ident not in completed:
                    todo_queue.put((ident, name, key, x))
                ident += 1
    total = ident
    print("found {} incomplete trials!".format(todo_queue.qsize(), flush=True))

    commit_queue = Queue()
    committer_p = Process(target=committer, args=(commit_queue,))
    committer_p.start()

    s = start_server(options.port)
    print("Starting to listen...", flush=True)
    s.listen(options.max_connections)
    processes = {}
    try:
        while True:
            c, addr = s.accept()
            p = Process(target=handler, args=(len(processes.keys()), c, todo_queue, total))
            p.start()
            processes[addr] = p
    except KeyboardInterrupt:
        print("Shutting down server!")

    commit_queue.put(None)
    committer_p.join()
    for p in processes.values():
        p.join()

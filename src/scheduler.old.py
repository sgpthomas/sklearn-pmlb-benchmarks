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

# todos = {}
todos = TodoList()
resultdir = "."
c_queue = None
count = 0
total = 0

def flatten(l):
    return [item for sublist in l for item in sublist]

def make_parser():
    descr = "Scheduler that hands out trials and collects results."
    parser = argparse.ArgumentParser(description=descr)

    parser.add_argument('resultdir', action="store")
    parser.add_argument('-p', '--port', action="store", default=3000, type=int)
    parser.add_argument('-m', '--max-connections', action="store", default=10, type=int)
    parser.add_argument('--default', action="store_true")
    parser.add_argument('--resume', action="store_true")

    return parser

# def commit_result(res, ident):
#     pd.DataFrame(res).to_pickle("{}/tmp-{}.pkl".format(resultdir, ident))

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

def committer():
    while True:
        item = c_queue.get()
        if item == None:
            print("Terminating committer!")
            break

        res, ident, remaining, percent = item
        pd.DataFrame(res).to_pickle("{}/tmp-{}.pkl".format(resultdir, ident))
        print("Commited #{} ({} remaining, {:.2%} completed)".format(ident, remaining, percent))

def handle_client(clients, key):
    try:
        c = clients[key]
        data = trial_msg.deserialize(c['client'].recv(trial_msg.SIZE))

        # check if client has died
        if data == None:
            print("Received 'None' from {}. Marked for removal!".format(c['client'].getsockname()[0]))
            return 1

        for data in data:
            # switch based on msg_type
            msg_type = data['msg_type']
            c['timeout'] = 0
            if msg_type == trial_msg.VERIFY:
                send_msg(c['client'], {'msg_type': trial_msg.SUCCESS})

            elif msg_type == trial_msg.TRIAL_REQUEST:
                ident, task = None, None
                item = todos.next()

                if item == None:
                    print("No more trials!")
                    send_msg(c['client'], {'msg_type': trial_msg.TERMINATE})
                    return

                ident, task = item
                dataset, method, params = task
                c['task'].add(ident)
                send_msg(c['client'], {'msg_type': trial_msg.TRIAL_DETAILS,
                                    'id': ident,
                                    'dataset': dataset,
                                    'method': method,
                                    'params': params})
                print("Handed out #{}: {} {} {}".format(ident, dataset, method, list(params.values())))

            elif msg_type == trial_msg.TRIAL_DONE:
                print("{} finished!".format(c['client'].getpeername()))
                ident = data['id']
                trial_result = data['data']

                todos.complete(ident)
                c_queue.put((trial_result, ident, len(todos.remaining()), len(todos.completed()) / todos.size()))
                # commit_result(trial_result, ident)
                # print("Commited #{} (remaining: {})".format(ident, len(todos.remaining())))

                send_msg(c['client'], {'msg_type': trial_msg.SUCCESS})
                c['task'].remove(ident)

            elif msg_type == trial_msg.TRIAL_CANCEL:
                print("{} aborted!".format(c['client'].getpeername()))
                ident = data['id']
                todos.cancel(ident)
                print("Aborting #{} ({} remaining)".format(ident, len(todos.remaining())))
                send_msg(c['client'], {'msg_type': trial_msg.SUCCESS})
                c['task'].remove(ident)

            elif msg_type == trial_msg.TERMINATE:
                return 1

            else:
                print("Unknown msg type: {}!".format(msg_type))
                send_msg(c['client'], {'msg_type': trial_msg.INVALID})
    except socket.timeout:
        clients[key]['timeout'] += 1
    except Exception as e:
        print("There was an exception while handling {}".format(c['client'].getsockname()))
        print(c)
        traceback.print_exc()

if __name__ == "__main__":
    options = make_parser().parse_args()

    try:
        os.mkdir(options.resultdir)
        # print(options.resultdir)
    except OSError:
        pass

    resultdir = options.resultdir

    # gather todos
    print("Gathering todos...", end='', flush=True)
    if options.default:
        params = {key: [{}] for key in classifier_functions}
    else:
        params = {key: item.get_pipeline_parameters()
                  for key, item in classifier_functions.items()}
    for name in classification_dataset_names:
        for key in sorted(params):
            for x in params[key]:
                todos.add((name, key, x))

    if options.resume:
        p = Path(resultdir)
        ids = list(map(lambda s: int(s.stem.split('-')[1]), p.glob("tmp-*.pkl")))
        for i in ids:
            todos.complete(i)

    total = todos.size()
    print("found {} incomplete trials!".format(len(todos.remaining())), flush=True)

    c_queue = Queue()
    committer_p = Process(target=committer)
    committer_p.start()

    clients = {}
    s = start_server(options.port)
    s.settimeout(1)
    print("Starting to listen...", flush=True)
    s.listen(options.max_connections)
    while len(todos.completed()) != todos.size():
        try:
            to_remove = []
            for k in clients:
                if clients[k]['timeout'] > 300:
                    to_remove.append(k)
                elif handle_client(clients, k) != None:
                    to_remove.append(k)
            for item in to_remove:
                print("Removing {}".format(item))
                if clients[item]['task'] != set():
                    for ident in clients[item]['task']:
                        todos.abort(ident)
                del clients[item]

            c, addr = s.accept()
            c.settimeout(0.2)
            clients[addr] = {'client': c, 'task': set(), 'timeout': 0}
            print("Connected to {}:{}!".format(addr[0], addr[1]))
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            print("Shutting down server!")
            c_queue.put(None)
            committer_p.join()
            print("Aborting progress on:")
            for item in todos.in_progress():
                print(" [-] {}".format(item))
            s.close()
            exit(0)
        sys.stdout.flush()
    print("No more todos!", flush=True)
    for item in todos.in_progress():
        print(" [-] {}".format(item), flush=True)

    c_queue.put(None)
    committer_p.join()

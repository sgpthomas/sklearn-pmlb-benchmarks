#!/usr/bin/env python3

import socket
import argparse
import trial_msg
import traceback
import multiprocessing
import sys
import os

import time

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
    "SGDClassifier": SGDClassifier, # 32500
    "SVC": SVC, # 1232
    "XGBClassifier": XGBClassifier # 30492
}

def make_parser():
    descr = "Client that executes trials that it receives from server.py"
    parser = argparse.ArgumentParser(description=descr)

    parser.add_argument('-o', "--host", action="store", default=None, type=str)
    parser.add_argument('-p', "--port", action="store", default=3000, type=int)
    parser.add_argument('--cpu', action="store", default=os.cpu_count(), type=int)
    parser.add_argument('--timeout', action="store", default=300, type=int)

    return parser

def connect_to_server(host, port):
    s = socket.socket()
    s.settimeout(20)
    s.connect((host, port))
    return s

def send_msg(scheduler, msg):
    scheduler.send(trial_msg.serialize(msg))

def recv_msg(scheduler, size=trial_msg.SIZE):
    return trial_msg.deserialize(scheduler.recv(size))

def expect_msg_type(scheduler, msg_type):
    data = recv_msg(scheduler)
    if len(data) != 1:
        raise Exception("Got multiple responses! {}".format(data))

    data = data[0]
    if data['msg_type'] != msg_type:
        raise Exception("Expected msg type '{}' but got '{}'".format(msg_type,
                                                                     data['msg_type']))

    return data

def send_expect_msg(scheduler, lock, msg, msg_type):
    lock.acquire()
    send_msg(scheduler, msg)
    data = expect_msg_type(scheduler, msg_type)
    lock.release()
    return data

def verify(scheduler, lock):
    msg = {'msg_type': trial_msg.VERIFY}
    send_expect_msg(scheduler, lock, msg, trial_msg.SUCCESS)
    print("Connected!")

def get_trial(scheduler, lock):
    msg = {'msg_type': trial_msg.TRIAL_REQUEST}
    # send_msg(scheduler, msg)
    # data = expect_msg_type(scheduler, trial_msg.TRIAL_DETAILS)
    data = send_expect_msg(scheduler, lock, msg, trial_msg.TRIAL_DETAILS)
    return data['id'], data['dataset'], data['method'], data['params']

def send_trial(scheduler, lock, ident, res):
    # packed = trial_msg.serialize(res)
    msg = {'msg_type': trial_msg.TRIAL_DONE,
           'id': ident,
           'data': res}
    # send_msg(scheduler, msg)
    # expect_msg_type(scheduler, trial_msg.TRIAL_SEND)
    send_expect_msg(scheduler, lock, msg, trial_msg.SUCCESS)
    # scheduler.send(packed)

def run_trial(scheduler, lock, ident, dataset, method, params):
    res = classifier_functions[method].run(dataset, params)
    send_trial(scheduler, lock, ident, res)

def terminate(scheduler):
    msg = {'msg_type': trial_msg.TERMINATE}
    send_msg(scheduler, msg)

if __name__ == "__main__":
    options = make_parser().parse_args()

    if options.host == None:
        options.host = socket.gethostname()

    try:
        scheduler = connect_to_server(options.host, options.port)
    except socket.timeout:
        print("Connection timed out! Is the host correct?")
        exit(-1)

    lock = multiprocessing.Lock()
    verify(scheduler, lock)

    processes = {}
    while True:
        try:
            # spawn new processes if needed
            while len(processes) < options.cpu:
                ident, dataset, method, params = get_trial(scheduler, lock)
                print(ident, dataset, method, params)
                f = lambda: run_trial(scheduler, lock, ident, dataset, method, params)
                p = multiprocessing.Process(target=f)
                p.start()
                processes[ident] = {'time': 0, 'process': p}

            to_remove = []
            for ident, info in processes.items():
                # check if process has died on it's own
                if not info['process'].is_alive():
                    to_remove.append(ident)

                # check if process has timed out
                elif info['time'] > options.timeout:

                    if lock.acquire(False):
                        print("Process {} timed out! Terminating!".format(info['process'].pid))
                        info['process'].terminate()
                        info['process'].join()
                        lock.release()
                        msg = {'msg_type': trial_msg.TRIAL_CANCEL,
                            'id': ident}
                        send_expect_msg(scheduler, lock, msg, trial_msg.SUCCESS)
                    else:
                        print("Process {} is communicating!".format(info['process'].pid))
                        lock.acquire()
                        lock.release()

                    to_remove.append(ident)


                # increment timer
                info['time'] += 1

            # remove all dead or timed out processes
            for ident in to_remove:
                del processes[ident]

            sys.stdout.flush()
            time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping!")
            break

    # while True:
    #     # the cancel message needs to send the id that failed
    #     try:
    #         p = multiprocessing.Process(target=lambda: run_trial(scheduler))
    #         p.start()
    #         p.join(300)

    #         if p.is_alive():
    #             print("Trial timed out! Forcefully terminating!")
    #             p.terminate()
    #             p.join()
    #             send_msg(scheduler, {'msg_type': trial_msg.TRIAL_CANCEL})
    #             expect_msg_type(scheduler, trial_msg.SUCCESS)
    #     except KeyboardInterrupt:
    #         print("Stopping!")
    #         break
    #     except Exception as e:
    #         send_msg(scheduler, {'msg_type': trial_msg.TRIAL_CANCEL})
    #         expect_msg_type(scheduler, trial_msg.SUCCESS)
    #         print("Something broke! Skipping this trial on this client!")
    #         traceback.print_exc()
    #     finally:
    #         sys.stdout.flush()
    #         if not options.loop:
    #             break

    terminate(scheduler)
    scheduler.close()


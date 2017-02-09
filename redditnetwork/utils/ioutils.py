import os
import cPickle as pickle
import json

def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory) 

def write_pickle(data, filename):
    fp = open(filename, "wb")
    pickle.dump(data, fp)

def load_pickle(filename):
    fp = open(filename, "rb")
    return pickle.load(fp)

def write_json(data, filename):
    fp = open(filename, "wb")
    json.dump(data, fp)

def load_json(filename):
    fp = open(filename, "rb")
    return json.load(fp)

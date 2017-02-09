import collections
import pandas as pd
import numpy as np
import os

from redditnetwork import constants
from redditnetwork.utils.ioutils import load_json


DATA = constants.DATA_HOME

def make_data_frame(communities, feature_dict):
    """
    Makes a pandas dataframe for name, months, and dictionary of feature funcs.
    Each feature func should take name and return feature value.
    Constructed dataframe has flat csv style structure and missing values are removed.
    """

    temp = collections.defaultdict(list)
    feature_dict["name"] = lambda name : name
    for name in communities:
        for feature, feature_func in feature_dict.iteritems():
            temp[feature].append(feature_func(name))
    df = pd.DataFrame(temp)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    return df

def make_data_frame_time(communities, time_range, feature_dict):
    """
    Makes a pandas dataframe for name, months, and dictionary of feature funcs.
    Each feature func should take (name, month) and return feature value.
    Constructed dataframe has flat csv style structure and missing values are removed.
    """

    temp = collections.defaultdict(list)
    feature_dict["name"] = lambda name, time : name
    feature_dict["time"] = lambda name, time : time
    for name in communities:
        for time in time_range:
            for feature, feature_func in feature_dict.iteritems():
                temp[feature].append(feature_func(name, time))
    df = pd.DataFrame(temp)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    return df


def read_filtered_users():
    users = set()
    with open(DATA + 'filtered_users.txt') as fp:
        for line in fp:
            x = line.strip().split('\t')
            users.add(x[0])
    return users

def read_subreddit_names(year=None):
    exclude_set = set(load_json(constants.DATA_HOME + "exclude_set.json"))
    subs = set([])
    if year == None:
        for year in constants.YEARS:
            subs.update([e.split(".")[0] for e in os.listdir(constants.DATA_HOME + "spacy_comments/" + str(year))])
    else:
        subs.update([e.split(".")[0] for e in os.listdir(constants.DATA_HOME + "spacy_comments/" + str(year))])
    return subs-exclude_set

def valid_subreddits():
    subreddits = []
    with open(DATA + "total_comment_counts.tsv") as fp:
        for line in fp:
            subreddits.append(line.split("\t")[0])
    return subreddits

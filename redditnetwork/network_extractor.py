import networkx as nx
import numpy as np

from collections import Counter, defaultdict

from redditnetwork.corpus_reader import PostMap, WeekIterWrapper, SpacyComments, MultiIterWrapper
from redditnetwork.utils.dateutils import get_week_timestamp

VEC_SIZE=300
SIF=10e-4

def extract_month_network_multisubreddits(subreddits, year, month):
    """
    Extracts a multilayer network of users comments and posts for
    multiple subreddits from the specified month.
    """
    post_map = {}
    for subreddit in subreddits:
        post_map.update(PostMap(subreddit, year, month).post_map)
    comment_iter = MultiIterWrapper([SpacyComments(subreddit, year, month) for
        subreddit in subreddits])
    return extract_network(post_map, comment_iter, 0)


def extract_week_network_multisubreddits(subreddits, year, week):
    """
    Extracts a multilayer network of users comments and posts for
    multiple subreddits from the specified week.
    """
    post_map = {}
    for subreddit in subreddits:
        post_map.update(PostMap(subreddit, year, -1, week=week).post_map)
    comment_iter = MultiIterWrapper([WeekIterWrapper(SpacyComments, week, subreddit, year) for
        subreddit in subreddits])
    return extract_network(post_map, comment_iter, 0)

def extract_year_network(subreddit, year):
    """
    Extracts a multi-layer network of users, comments, and posts.
    Data is taken from a specific month (num between 1 and 12) in a specific year.
    """
    post_map = {}
    for month in range(1,13):
        post_map.update(PostMap(subreddit, year, month).post_map)
    comment_iter = MultiIterWrapper([SpacyComments(subreddit, year, month) for
        month in range(1,13)])
    base_time = get_week_timestamp(year,0)
    return extract_network(post_map, comment_iter, base_time)


def extract_month_network(subreddit, year, month):
    """
    Extracts a multi-layer network of users, comments, and posts.
    Data is taken from a specific month (num between 1 and 12) in a specific year.
    """
    post_map = PostMap(subreddit, year, month)
    comment_iter = SpacyComments(subreddit, year, month)
    #TODO: Actually do this... It is not a big deal since the values
    # will be internally consistent, but still...
    month_base_time = get_week_timestamp(year, month/4-2)
    return extract_network(post_map.post_map, comment_iter, month_base_time)

def extract_week_network(subreddit, year, week):
    """
    Extracts a multi-layer network of users, comments, and posts.
    Data is taken from a specific week (num between 1 and 50) in a specific year.
    """
    post_map = PostMap(subreddit, year, -1, week=week)
    comment_iter = WeekIterWrapper(SpacyComments, week, subreddit, year)
    week_base_time = get_week_timestamp(year, week)

    return extract_network(post_map.post_map, comment_iter, week_base_time)

def _get_embedding(doc, counter, total_count):
    vecs = [word.vector*(SIF / (counter[word.lower_]/total_count + SIF)) for word in doc if word.has_vector]
    if len(vecs) == 0 or np.isnan(np.sum(np.array(vecs))):
        return np.zeros((VEC_SIZE,))
    else:
        vecs = np.array(vecs)
        vecs = np.mean(vecs, axis=0)
        return vecs

def extract_network(post_map, comment_iter, base_time, idf=True):

    if idf:
        df = Counter()
        total_count = 0.
        for comment in comment_iter:
            for word in comment["doc"]:
                df[word.lower_] += 1
                total_count += 1.
    else:
        df = defaultdict(float)
        total_count = 1.

    graph = nx.DiGraph(user_feats={},
            post_feats = {"score" : 1, "time": 1, "num_comments": 1, "subreddit" : 1, "length" : 1, "word_vecs" : VEC_SIZE},
            comment_feats = {"score" : 1, "time" : 1, "post_time_offset": 1, "length" : 1, "subreddit" : 1, "word_vecs" : VEC_SIZE})

    ## Add all posts as nodes connected to their authors
    for post in post_map.values():
        graph.add_node(post["id"], 
                type="post",
                score=post["score"],
                num_comments=post["num_comments"],
                subreddit=post["subreddit"],
                time=(int(post["timestamp"])-base_time)/3600.,
                length=len(post["doc"]),
                word_vecs=_get_embedding(post["doc"], df, total_count))
        if not graph.has_node(post["author"]):
            graph.add_node(post["author"], type="user")
        graph.add_edge(post["author"], post["id"], type="user_post")

    skipped_missing_parent = 0
    skipped_missing_post = 0
    for i, comment in enumerate(comment_iter):
        # skip comments that don't respond to a post from this week
        if not comment["post"] in post_map:
            skipped_missing_post += 1
            continue
        # skip comments that don't respond to a  parent from this week
        if comment["parent"] != comment["post"] and not graph.has_node(comment["parent"]):
            skipped_missing_parent += 1
            continue

        # add author node if necessary
        if not graph.has_node(comment["author"]):
            graph.add_node(comment["author"], type="user")

        # add comment node
        graph.add_node(comment["id"],
                type="comment",
                score=comment["score"],
                subreddit=comment["subreddit"],
                time=(comment["timestamp"]-base_time)/3600.,
                post_time_offset=(comment["timestamp"]-int(post["timestamp"]))/3600.,
                length=len(comment["doc"]),
                word_vecs=_get_embedding(comment["doc"], df, total_count))

        # Add edges
        graph.add_edge(comment["author"], comment["id"], type="user_comment")
        if comment["parent"] != comment["post"]:
            graph.add_edge(comment["parent"], comment["id"], type="comment_comment")
        else:
            graph.add_edge(comment["post"], comment["id"], type="post_comment")

    print "Processed {:d} comments, of which {:d} were removed for missing post and {:d} for missing parent".format(
            i, skipped_missing_post, skipped_missing_parent)
    return graph 

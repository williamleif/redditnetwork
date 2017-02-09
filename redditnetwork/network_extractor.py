import networkx as nx
from redditnetwork.corpus_reader import PostMap, WeekIterWrapper, SpacyComments
from redditnetwork.utils.dateutils import get_week_timestamp


def extract_week_network(subreddit, year, week):
    """
    Extracts a multi-layer network of users, comments, and posts.
    Data is taken from a specific week (num between 1 and 50) in a specific year.
    """

    graph = nx.DiGraph(user_feats={},
            post_feats = {"score" : 1, "time": 1, "word_vec" : 300},
            comment_feats = {"score" : 1, "time" : 1, "time_offset": 1, "length" : 1, "word_vec" : 300})
    post_map = PostMap(subreddit, year, -1, week=week)
    comment_iter = WeekIterWrapper(SpacyComments, week, subreddit, year)
    week_base_time = get_week_timestamp(year, week)

    ## Add all posts as nodes connected to their authors
    for post in post_map.post_map.values():
        graph.add_node(post["id"], 
                type="post",
                score=post["score"],
                time=(int(post["timestamp"])-week_base_time)/3600.,
                word_vecs = post["doc"].vector)
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
                time=(comment["timestamp"]-week_base_time)/3600.,
                time_offset=(comment["timestamp"]-int(post["timestamp"]))/3600.,
                length=len(comment["doc"]),
                word_vecs=comment["doc"].vector)

        # Add edges
        graph.add_edge(comment["author"], comment["id"], type="user_comment")
        if comment["parent"] != comment["post"]:
            graph.add_edge(comment["parent"], comment["id"], type="comment_comment")
        else:
            graph.add_edge(comment["post"], comment["id"], type="post_comment")

    print "Processed {:d} comments, of which {:d} were removed for missing post and {:d} for missing parent".format(
            i, skipped_missing_post, skipped_missing_parent)
    return graph 

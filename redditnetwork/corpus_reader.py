"""
Various objects for iterating over and accessing processed Reddit data.
"""

import json

from redditnetwork import constants
from redditnetwork.utils.datautils import read_filtered_users
from redditnetwork.utils.stringutils import is_bot
from redditnetwork.utils.dateutils import get_week

from spacy.tokens.doc import Doc
from spacy.en import English

SPACY_VOCAB = English().vocab
FILTERED_USERS = read_filtered_users()

class WeekIterWrapper():
    """
    Gets an iterator over a specific week.
    Takes a comment or post iterator class as an argument.
    Annoyingly weeks and months are not aligned....
    """
    def __init__(self, cls, week, subreddit, year, **kw_args):
        # Throws an assertion if you try to get weeks that cross between
        # years
        assert week != 0 and week < 51
        self.week = week
        month = week / 4 + 1
        ## Week 1 for us == week 2 for ISO weeks
        self.iter1 = cls(subreddit, year, month, **kw_args)
        self.iter2 = cls(subreddit, year, month+1, **kw_args)

    def __iter__(self):
        for item in self.iter1.__iter__(week=self.week):
            yield item
        for item in self.iter2.__iter__(week=self.week):
            yield item

class PostMap():
    """
    Map into post data.
    """
    def __init__(self, subreddit, year, month, week=None, path=None,
            clean_deleted=True, clean_bots=True):
        if path == None:
            path = constants.DATA_HOME + "spacy_posts/"
        if not week is None:
            print "Warning: Using week argument and ignoring month"
            self.post_map = self._make_map(
                    WeekIterWrapper(PostIterator, week, subreddit, 
                        year, path=path, 
                        clean_deleted=True, clean_bots=True))
        else:
            self.post_map = self._make_map(
                    PostIterator(subreddit, year, month, path=path, 
                        clean_deleted=True, clean_bots=True))

    def _make_map(self, info_iterator):
        post_map = {}
        for entry in info_iterator:
            post_map[entry["id"]] = entry
        return post_map

    def get_post(self, id):
        return self.post_map[id]

    def __getitem__(self, id):
        return self.get_post(id)

    def __contains__(self, id):
        return id in self.post_map


class PostIterator():
    """
    Iterator over post metadata only
    """
    def __init__(self, subreddit, year, month, path=None, 
            clean_deleted=True, clean_bots=True):
        if path == None:
            path = constants.DATA_HOME + "spacy_posts/"
        path += "{:d}_{:02d}/".format(year, month) + subreddit
        self._vocab = SPACY_VOCAB
        self.path = path
        self._len = None
        self.clean_bots = clean_bots
        self.clean_deleted = clean_deleted

    def _parse_info(self, line):
        info = json.loads(line)
        return info

    def __len__(self):
        if self._len == None:
            i = -1
            with open(self.path + ".info") as fp:
                for i, _ in enumerate(fp):
                    pass
            self._len = i + 1
        return self._len

    def __iter__(self, week=None):
        with open(self.path + ".info")  as info:
            with open(self.path + ".title.bin") as title_bin:
                for byte_string in Doc.read_bytes(title_bin):
                    info_line = info.readline()
                    comment_info = self._parse_info(info_line)
                    if not (week is None) and get_week(comment_info["timestamp"]) != week:
                        continue
                    if self.clean_deleted and comment_info["author"] == "[deleted]":
                        continue
                    if self.clean_bots and (is_bot(comment_info["author"]) or 
                        comment_info["author"] in FILTERED_USERS):
                        continue
                    comment_info["doc"] = Doc(self._vocab).from_bytes(byte_string)
                    yield comment_info


class InfoIterator():
    """
    Iterator over comment metadata only
    """
    def __init__(self, subreddit, year, month=None, path=None,
            clean_deleted=True, clean_bots=True):
        if path == None:
            path = constants.DATA_HOME + "spacy_comments/"
     #   self._vocab = Vocab.load(path + u"vocab.bin")
        # Annoyingly inefficient but necessary for now
        if not month is None:
            path += "{:d}_{:02d}/".format(year, month) + subreddit
        else:
            path += "{:d}/".format(year) + subreddit
        self.path = path
        self._len = None
        self.clean_deleted = clean_deleted
        self.clean_bots = clean_bots

    def _parse_info(self, line):
        info = line.split("\t")
        comment_info = {"id" : info[0],
                "timestamp" : int(info[1]),
                "author" : info[2],
                "score" : int(info[3]),
                "parent" : info[4], 
                "post" : info[5].strip()}
        return comment_info

    def __len__(self):
        if self._len == None:
            i = -1
            with open(self.path + ".info") as fp:
                for i, _ in enumerate(fp):
                    pass
            self._len = i + 1
        return self._len

    def __iter__(self):
        with open(self.path + ".info")  as info:
            for line in info:
                comment_info = self._parse_info(line)
                if self.clean_deleted and comment_info["author"] == "[deleted]":
                    continue
                if self.clean_bots and (is_bot(comment_info["author"]) or 
                    comment_info["author"] in FILTERED_USERS):
                    continue
                yield comment_info

class SpacyComments():
    """
    Iterator over spacy comments.
    """

    def __init__(self, subreddit, year, month=None, path=None, 
            include_punct=True, down_sample=None, clean_bots=True, clean_deleted=True):
        if path == None:
            path = constants.DATA_HOME + "spacy_comments/"
        self._vocab = SPACY_VOCAB
        if not month is None:
            path += "{:d}_{:02d}/".format(year, month) + subreddit
        else:
            path += "{:d}/".format(year) + subreddit
        self.path = path
        self._len = None
        self.clean_bots = clean_bots
        self.clean_deleted = clean_deleted
        self.include_punct = include_punct

    def _spacy_string_clean(self, token):
        if token.like_url:
            return "<URL>"
        elif token.like_num:
            return "<NUM>"
        elif (not self.include_punct) and token.is_punct and (not token.tag_ == "."):
            return ""
        else:
            return token.lower_

    def _text_from_doc(self, doc):
        return " ".join([self._spacy_string_clean(token) for token in doc])

    def _parse_info(self, line):
        info = line.split("\t")
        comment_info = {"id" : info[0],
                "timestamp" : int(info[1]),
                "author" : info[2],
                "score" : int(info[3]),
                "parent" : info[4], 
                "post" : info[5].strip()}
        return comment_info

    def __len__(self):
        if self._len == None:
            with open(self.path + ".info") as fp:
                for i, _ in enumerate(fp):
                    pass
            self._len = i + 1
        return self._len

    def __iter__(self, week=None):
        with open(self.path + ".bin", "rb") as bin:
            with open(self.path + ".info")  as info:
                for byte_string in Doc.read_bytes(bin):
                    comment_info = self._parse_info(info.next())
                    if (not week is None) and get_week(comment_info["timestamp"]) != week:
                        continue
                    if self.clean_deleted and comment_info["author"] == "[deleted]":
                        continue
                    if self.clean_bots and (is_bot(comment_info["author"]) or 
                        comment_info["author"] in FILTERED_USERS):
                        continue
                    doc = Doc(self._vocab).from_bytes(byte_string)
                    comment_info["doc"] = doc
                    comment_info["text"] = self._text_from_doc(doc)
                    yield comment_info

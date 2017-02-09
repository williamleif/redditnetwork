import string
import nltk
import re

NLTK_STOP = set(nltk.corpus.stopwords.words('english'))
PUNCTUATION = set(string.punctuation)
URL = ['www', '.com', '.net', '.org', '.edu', '//', '/u/', '/r/', 'http']
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
HTTP = re.compile("https?$")
BOT = re.compile("bot\d*$")

def is_bot(word):
    word = word.lower()
    return bool(BOT.search(word))

def is_punkt(word):
    return word in PUNCTUATION

def is_http(word):
    return bool(HTTP.match(word))

def has_numbers(input_string):
    return bool(re.search(r'\d', input_string))

def is_ascii(s):
    try:
        s.decode("ascii")
    except UnicodeEncodeError:
        return False
    else:
        return True

def is_url(word):
    b = [1 if t in word else 0 for t in URL]
    return sum(b) > 0

def clean_word_replace(word):
    word = word.strip()
    word = word.strip(string.punctuation)
    word = word.lower()
    if not is_ascii(word):
        return "<SPECIAL>"
    elif is_http(word):
        return "<URL>"
    elif has_numbers(word):
        return "<NUM>"
    else:
        return word

def clean_word(word, lower=True, stem=True, remove_stop=True):
    word = word.strip()
    word = word.strip(string.punctuation)
    w = word.lower()
    if remove_stop:
        if word.startswith("'"):
            return ""
        if not is_ascii(word):
            return ""
        b = [1 if t in word else 0 for t in URL]
        if sum(b) > 0:
            return ""
        if w in PUNCTUATION or w in NLTK_STOP:
            return ""
        if has_numbers(w):
            return ""
    if stem:
        w = lemmatizer.lemmatize(w) # for nouns
        w = lemmatizer.lemmatize(w, pos = 'v') # for verbs
    return w

def is_stop(word):
    if len(word) == 1:
        return True
    elif word.isdigit():
        return True
    elif word in NLTK_STOP:
        return True
    else:
        return False

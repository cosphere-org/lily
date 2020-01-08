
import os
import json


class StopWordsFilter:

    def __init__(self):

        base_dir = os.path.dirname(__file__)

        self.stopwords = {}

        # -- polish
        with open(os.path.join(base_dir, 'pl.json'), 'r') as f:
            self.stopwords['polish'] = set(json.loads(f.read()))

    def is_stopword(self, conf, word):
        if conf == 'polish':
            return word in self.stopwords[conf]

        # -- all other languages are treated the same
        return False


stopwords_filter = StopWordsFilter()

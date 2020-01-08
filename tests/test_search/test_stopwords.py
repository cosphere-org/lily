
from django.test import TestCase

from search.stopwords import stopwords_filter


class StopWordsFilterTestCase(TestCase):

    def test_is_stopword__polish(self):

        assert stopwords_filter.is_stopword(
            'polish', 'jak') is True
        assert stopwords_filter.is_stopword(
            'polish', 'ale') is True
        assert stopwords_filter.is_stopword(
            'polish', 'albo') is True
        assert stopwords_filter.is_stopword(
            'polish', 'wszędzie') is False
        assert stopwords_filter.is_stopword(
            'polish', 'cześć') is False

    def test_is_stopword__non_polish(self):

        assert stopwords_filter.is_stopword(
            'english', 'hi') is False
        assert stopwords_filter.is_stopword(
            'english', 'and') is False
        assert stopwords_filter.is_stopword(
            'english', 'or') is False
        assert stopwords_filter.is_stopword(
            'english', 'what') is False

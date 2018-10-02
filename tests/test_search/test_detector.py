
from unittest import TestCase

import pytest

from lily.search.detector import LanguageDetector
from lily.base.events import EventFactory


class LanguageDetectorTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        self.detector = LanguageDetector()

    #
    # DETECT_LANGUAGE
    #
    def test_detect_language(self):

        self.mocker.patch.object(
            self.detector.identifier, 'rank'
        ).return_value = [
            ('en', 0.9),
            ('de', 0.4),
        ]

        assert self.detector.detect('hello world') == [
            {'abbr': 'en', 'name': 'English'},
            {'abbr': 'de', 'name': 'German'},
        ]

    def test_detect_language__limit_by_probability(self):

        self.mocker.patch.object(
            self.detector.identifier, 'rank'
        ).return_value = [
            ('en', 0.9),
            ('fr', 0.6),
            ('de', 0.55)
        ]
        self.mocker.patch.object(self.detector, 'DETECT_THRESHOLD_LEN', 5)

        assert self.detector.detect('hello world') == [
            {'abbr': 'en', 'name': 'English'},
            {'abbr': 'fr', 'name': 'French'},
            {'abbr': 'de', 'name': 'German'},
        ]

    def test_detect_language__no_machted(self):

        self.mocker.patch.object(
            self.detector.identifier, 'rank'
        ).return_value = []

        try:
            self.detector.detect('hi world')

        except EventFactory.BrokenRequest as e:
            assert e.data == {
                '@event': 'UNSUPPORTED_LANGUAGE_DETECTED',
                '@type': 'error',
                'text': 'hi world',
                'user_id': None,
            }

        else:
            raise AssertionError('should raise exception')

    def test_detect_language__limit_by_length(self):

        self.mocker.patch.object(
            self.detector.identifier, 'rank'
        ).return_value = [
            ('en', 0.9),
            ('fr', 0.6),
            ('de', 0.55),
            ('es', 0.1),
        ]
        self.mocker.patch.object(self.detector, 'DETECT_THRESHOLD_LEN', 2)

        assert self.detector.detect('hello world') == [
            {'abbr': 'en', 'name': 'English'},
            {'abbr': 'fr', 'name': 'French'},
        ]

    def test_detect_language__no_results(self):

        self.mocker.patch.object(
            self.detector.identifier, 'rank'
        ).return_value = []

        try:
            self.detector.detect('hello world')

        except EventFactory.BrokenRequest as e:
            assert e.data == {
                '@event': 'UNSUPPORTED_LANGUAGE_DETECTED',
                '@type': 'error',
                'text': 'hello world',
                'user_id': None,
            }

        else:
            raise AssertionError('should raise exception')

    #
    # DETECT_DB_CONF
    #
    def test_detect_db_conf__returns_simple_cases(self):

        conf = LanguageDetector().detect_db_conf('orange')

        assert conf == 'english'

    def test_detect_db_conf__returns_detect_results(self):

        # 1st call with portuguese
        conf = LanguageDetector().detect_db_conf(
            'Cómo estás, cuál es tu nombre')

        assert conf == 'spanish'

        # 2nd call with english
        conf = LanguageDetector().detect_db_conf(
            'hello man how are you doing')

        assert conf == 'english'

        # 3rd call with Esperanto
        conf = LanguageDetector().detect_db_conf('hallo wie gehts')

        assert conf == 'german'

    def test_detect_db_conf__min_detection_length(self):

        conf = LanguageDetector().detect_db_conf('wat!')

        assert conf == 'simple'

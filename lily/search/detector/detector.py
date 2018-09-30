
import os

from yaml import load
from langid.langid import LanguageIdentifier, model

from lily.base.events import EventFactory


def load_from_data(filename):

    filepath = os.path.join(
        os.path.dirname(__file__),
        'data',
        filename)

    return load(open(filepath, 'r'))


LANGUAGE_TO_CONFIGURATION = load_from_data(
    'language_to_configuration_map.yaml')


ALL_LANGUAGES = load_from_data(
    'language_codes.yaml')


class LanguageDetector(EventFactory):

    DETECT_THRESHOLD_PROB = 0.3
    """
    Consider only those languages that have rank probability higher that 0.3

    """

    DETECT_THRESHOLD_LEN = 3
    """
    Consider maximum 3 detected languages.

    """

    DETECT_MIN_LANG_LENGTH = 5
    """
    Minimum length of text which will trigger the language detection mechanism.
    Every text with length below this threshold automatically is treated as
    following ``simple`` configuration.

    """

    # -- languages supported by langid
    language_abbrs = set([
        'af', 'am', 'an', 'ar', 'as', 'az', 'be', 'bg', 'bn', 'br', 'bs',
        'ca', 'cs', 'cy', 'da', 'de', 'dz', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'fi', 'fo', 'fr', 'ga', 'gl', 'gu', 'he', 'hi', 'hr',
        'ht', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'jv', 'ka', 'kk', 'km',
        'kn', 'ko', 'ku', 'ky', 'la', 'lb', 'lo', 'lt', 'lv', 'mg', 'mk',
        'ml', 'mn', 'mr', 'ms', 'mt', 'nb', 'ne', 'nl', 'nn', 'no', 'oc',
        'or', 'pa', 'pl', 'ps', 'pt', 'qu', 'ro', 'ru', 'rw', 'se', 'si',
        'sk', 'sl', 'sq', 'sr', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr',
        'ug', 'uk', 'ur', 'vi', 'vo', 'wa', 'xh', 'zh', 'zu'
    ])

    identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

    def __init__(self):

        self.languages = [
            l
            for l in ALL_LANGUAGES
            if l['abbr'] in self.language_abbrs]

    def detect(self, text):

        language_abbrs = set([
            lang
            for lang, prob in self.identifier.rank(text)
            if prob > self.DETECT_THRESHOLD_PROB
        ][:self.DETECT_THRESHOLD_LEN])

        if not language_abbrs:
            raise self.BrokenRequest(
                'UNSUPPORTED_LANGUAGE_DETECTED',
                data={'text': text},
                is_critical=True)

        return [
            l
            for l in self.languages
            if l['abbr'] in language_abbrs]

    def detect_db_conf(self, text):

        text = text.strip()
        if len(text) < self.DETECT_MIN_LANG_LENGTH:
            return 'simple'

        try:
            detected = self.detect(text)[0]['abbr']

            return LANGUAGE_TO_CONFIGURATION[detected]['configuration']

        except (KeyError, IndexError, self.BrokenRequest):
            return 'simple'


detector = LanguageDetector()

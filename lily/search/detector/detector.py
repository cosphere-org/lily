# -*- coding: utf-8 -*-

import os

from django.conf import settings
from yaml import load
import detectlanguage


BASE_DIR = os.path.dirname(__file__)


LANGUAGE_TO_CONFIGURATION = load(
    open(os.path.join(BASE_DIR, 'language_to_configuration_map.yaml'), 'r'))


MIN_LANG_DETECTION_TEXT_LENGTH = 5
"""
Minimum length of text which will trigger the language detection mechanism.
Every text with length below this threshold automatically is treated as
following ``simple`` configuration.

"""

detectlanguage.configuration.api_key = settings.DETECT_LANGUAGE_API_KEY


def get_search_conf_language(text):

    text = text.strip()
    if len(text) < MIN_LANG_DETECTION_TEXT_LENGTH:
        return 'simple'

    try:
        detected = detectlanguage.simple_detect(text)
        return LANGUAGE_TO_CONFIGURATION[detected]['configuration']

    except (KeyError, IndexError):
        return 'simple'

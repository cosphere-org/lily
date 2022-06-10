
import re
import os
import json
import logging

from django.template import engines


BASE_DIR = os.path.dirname(__file__)


BASE_TEMPLATE_PATH = os.path.join(BASE_DIR, './base.md')


engine = engines['django']


logger = logging.getLogger('RENDERER')


def clean_extra_indents(x):
    return re.sub(r'\n +', r'\n', x)


def clean_extra_new_lines(x):
    return re.sub(r'\n+', r'\n', x)


def dump_or_none(x):
    if x:
        return json.dumps(x, indent=4, sort_keys=True)


import re
import os
import json
import logging
from collections import OrderedDict

from django.template import engines

from lily.entrypoint.base import BaseRenderer
from lily.base.meta import MetaSerializer
from lily.base.test import get_examples_filepath


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

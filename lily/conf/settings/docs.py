# -*- coding: utf-8 -*-

import os


BASE_DIR = os.path.dirname(__file__)

DOCS_TEST_EXAMPLES_FILE = os.path.join(
    BASE_DIR, '../../docs', 'test_examples.json')

DOCS_OPEN_API_SPEC_FILE = os.path.join(
    BASE_DIR, '../../docs', 'open_api_spec.json')

DOCS_COMMANDS_CONF_FILE = os.path.join(
    BASE_DIR, '../../docs', 'commands_conf.json')

DOCS_MARKDOWN_SPEC_FILE = os.path.join(
    BASE_DIR, '../../../', 'DOCS.md')

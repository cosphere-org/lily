# -*- coding: utf-8 -*-

import re
import os
import json
import logging
from collections import OrderedDict

from django.template import engines
from django.conf import settings

from .views_index_renderer import Renderer as ViewsIndexRender


BASE_DIR = os.path.dirname(__file__)


BASE_TEMPLATE_PATH = os.path.join(BASE_DIR, './markdown_spec_base.md')


engine = engines['django']


logger = logging.getLogger('RENDERER')


def clean_extra_indents(x):
    return re.sub(r'\n +', r'\n', x)


def clean_extra_new_lines(x):
    return re.sub(r'\n+', r'\n', x)


def dump_or_none(x):
    if x:
        return json.dumps(x, indent=4, sort_keys=True)


class Renderer:

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):

        views_index = ViewsIndexRender(self.urlpatterns).render()

        with open(BASE_TEMPLATE_PATH, 'r') as f:
            template = engine.from_string(f.read())

        examples = self.get_examples()
        document_tree = {}

        for path, conf in views_index.items():
            for method in ['post', 'get', 'put', 'delete']:
                try:
                    method_conf = conf[method]

                except KeyError:
                    pass

                else:
                    meta = method_conf['meta'].serialize()
                    name = method_conf['name']

                    # -- currently we only take into account first tag!
                    tag = meta['tags'][0]
                    document_tree.setdefault(tag, [])

                    try:
                        command_examples = examples[name]

                    except KeyError:
                        logger.error('Missing examples for {}'.format(name))

                    else:
                        document_tree[tag].append({
                            'title': '{name}: {method} {path}'.format(
                                name=name,
                                method=method.upper(),
                                path=conf['path_conf']['path']),
                            'description': clean_extra_indents(
                                '{title} \n {description}'.format(
                                    title=meta['title'],
                                    description=meta['description'])),
                            'calls': sorted([
                                {
                                    'title': t,
                                    'response': {
                                        'content': dump_or_none(
                                            e['response']['content']),
                                    },
                                    'request': {
                                        'method': method,
                                        'path': e['request']['path'],
                                        'content': dump_or_none(
                                            e['request'].get('content')),
                                        'headers': self.render_headers(e)
                                    }
                                }
                                for t, e in command_examples.items()
                            ], key=lambda x: x['title'])
                        })

        return clean_extra_new_lines(template.render({
            'document_tree': OrderedDict(
                sorted(document_tree.items(), key=lambda x: x[0])),
        }))

    def render_headers(self, e):
        return OrderedDict(sorted(
            e['request'].get('headers', {}).items(),
            key=lambda x: x[0]))

    def get_examples(self):
        with open(settings.DOCS_TEST_EXAMPLES_FILE) as f:
            return json.loads(f.read())


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


class MarkdownRenderer(BaseRenderer):

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):

        base_index = super(MarkdownRenderer, self).render()

        with open(BASE_TEMPLATE_PATH, 'r') as f:
            template = engine.from_string(f.read())

        examples = self.get_examples()
        document_tree = {}
        sorted_index = sorted(
            base_index.items(), key=lambda x: x[0])

        for command_name, conf in sorted_index:
            meta = MetaSerializer(conf['meta']).data

            domain = meta['domain']['name']
            document_tree.setdefault(domain, [])

            try:
                command_examples = examples[command_name]

            except KeyError:
                logger.error(
                    'Missing examples for {}'.format(command_name))

            else:
                document_tree[domain].append({
                    'title': '{name}: {method} {path}'.format(
                        name=command_name,
                        method=conf['method'].upper(),
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
                                'method': conf['method'],
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
        with open(get_examples_filepath()) as f:
            return json.loads(f.read())

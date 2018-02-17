# -*- coding: utf-8 -*-

import os
import json

import yaml
from django.template import engines
from django.conf import settings

from ..base.schema import to_schema
from .views_index_renderer import Renderer as ViewsIndexRender


BASE_DIR = os.path.dirname(__file__)


BASE_TEMPLATE_PATH = os.path.join(BASE_DIR, './open_api_spec_base.yaml')


engine = engines['django']


class Renderer:

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):

        views_index = ViewsIndexRender(self.urlpatterns).render()

        with open(BASE_TEMPLATE_PATH, 'r') as f:
            template = engine.from_string(f.read())

        return template.render({
            'version': '1.0.0',
            'paths': self.to_yaml(self.render_paths(views_index)),
        })

    def to_yaml(self, data, spaces_count=4):
        raw_yaml = yaml.dump(data, default_flow_style=False, indent=4)
        return raw_yaml.replace('\n', '\n' + spaces_count * ' ')

    def render_paths(self, views_index):

        paths = {}
        examples = self.get_examples()

        for path, conf in views_index.items():
            commands = {
                'parameters': conf['path_conf']['parameters']
            }
            for method in ['post', 'get', 'put', 'delete']:
                try:
                    method_conf = conf[method]

                except KeyError:
                    # FIXME: test it!
                    # FIXME: create a WARNING to info the creator about
                    # some of the views which are still not translated
                    # to the new format
                    continue

                else:
                    # -- input parser
                    # body_parser = method_conf['input'].body_parser

                    # -- output serializer
                    serializer = method_conf['output'].serializer

                    meta = method_conf['meta'].serialize()
                    name = method_conf['name']
                    responses = {}
                    try:
                        path_examples = examples[name]

                    except KeyError:
                        # FIXME: Error that some methods have no examples
                        # meaning that they have no tests
                        pass

                    else:
                        responses = {
                            t: {
                                'description': e['description'],
                                'content': {
                                    e['response']['content_type']: {
                                        'schema': dict(
                                            title=serializer.__name__,
                                            example=e['response']['content'],
                                            **to_schema(serializer)),
                                    }
                                }
                            }
                            for t, e in path_examples.items()
                            if e['method'] == method
                        }

                    commands[method] = {
                        'operationId': method_conf['name'],
                        'summary': meta['title'],
                        'tags': meta['tags'],
                        'description': meta['description'],
                    }

                    if responses:
                        commands[method]['responses'] = responses

            paths[conf['path_conf']['path']] = commands

        return paths

    def get_examples(self):
        with open(settings.LILY_DOCS_TEST_EXAMPLES_FILE) as f:
            return json.loads(f.read())

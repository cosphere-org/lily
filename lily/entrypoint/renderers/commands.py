# -*- coding: utf-8 -*-

from importlib import import_module
import json
import re

from django.conf import settings

from .base import BaseRenderer
from .schema import SchemaRenderer


class CommandsRenderer(BaseRenderer):

    def __init__(self, with_examples=False):
        self.urlpatterns = self.get_urlpatterns()

        self.with_examples = with_examples
        if with_examples:
            self.examples = self.get_all_examples()

        else:
            self.examples = {}

    def get_urlpatterns(self):
        return import_module(settings.ROOT_URLCONF).urlpatterns

    def render(self):

        commands_index = super(CommandsRenderer, self).render()
        rendered = {}

        for name, conf in commands_index.items():

            path_conf = conf['path_conf']
            method = conf['method']
            meta = conf['meta']
            access = conf['access']
            input_ = conf['input']
            output = conf['output']
            source = conf['source']

            configuration = {
                'method': method,
                'path_conf': path_conf,
                'meta': meta,
                'source': source,
                'access': access,
            }

            # -- EXAMPLES
            if self.with_examples:
                configuration['examples'] = self.get_examples(
                    name, path_conf.pop('pattern'))

            # -- SCHEMAS
            schemas = {}
            schemas['output'] = SchemaRenderer(
                output.serializer).render().serialize()

            if input_.query_parser:
                schemas['input_query'] = SchemaRenderer(
                    input_.query_parser).render().serialize()

            if input_.body_parser:
                schemas['input_body'] = SchemaRenderer(
                    input_.body_parser).render().serialize()

            configuration['schemas'] = schemas
            rendered[name] = configuration

        return rendered

    def get_all_examples(self):
        # FIXME: !!!!! change the name of the file --> maybe store directly in
        # the module!!! --> check based on the caching mechanism!!!
        with open(settings.LILY_DOCS_TEST_EXAMPLES_FILE) as f:
            return json.loads(f.read())

    def get_examples(self, command_name, path_pattern):
        try:
            examples = self.examples[command_name]

        except KeyError:
            return {}

        else:
            for example in examples.values():
                path = example['request']['path']
                parameters = re.compile(path_pattern).search(path)
                example['request']['parameters'] = parameters.groupdict()

            return examples

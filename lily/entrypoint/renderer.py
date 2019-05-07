
from importlib import import_module
import json
import os
import re
import sys

from lily.conf import settings
from lily.base.test import get_examples_filepath
from .base import BaseRenderer
from .schema import SchemaRenderer


class CommandsRenderer(BaseRenderer):

    def __init__(self):
        self.urlpatterns = self.get_urlpatterns()
        self.examples = self.get_all_examples()

    def get_urlpatterns(self):

        # -- make sure that the main directory is also visible during
        # -- the search of all url patterns
        sys.path.insert(0, os.getcwd())

        return import_module(settings.ROOT_URLCONF).urlpatterns

    def render(self):

        commands_index = super(CommandsRenderer, self).render()
        rendered = {}
        enums = []

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
            pattern = path_conf.pop('pattern')
            configuration['examples'] = self.get_examples(name, pattern)

            # -- SCHEMAS
            schemas = {}
            output_schema = SchemaRenderer(output.serializer).render()
            schemas['output'] = output_schema.serialize()
            enums.extend(output_schema.enums)

            if input_.query_parser:
                input_query_schema = (
                    SchemaRenderer(input_.query_parser).render())
                schemas['input_query'] = input_query_schema.serialize()
                enums.extend(input_query_schema.enums)

            if input_.body_parser:
                input_body_schema = SchemaRenderer(input_.body_parser).render()
                schemas['input_body'] = input_body_schema.serialize()
                enums.extend(input_body_schema.enums)

            configuration['schemas'] = schemas
            rendered[name] = configuration

        rendered['@enums'] = self.unique_enums(enums)
        return rendered

    def unique_enums(self, enums):
        unique_enums = set(
            [json.dumps(enum, sort_keys=True) for enum in enums])

        return sorted(
            [json.loads(enum) for enum in unique_enums],
            key=lambda x: x['enum_name'])

    def get_all_examples(self):
        try:
            with open(get_examples_filepath()) as f:
                return json.loads(f.read())

        except FileNotFoundError:
            return {}

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
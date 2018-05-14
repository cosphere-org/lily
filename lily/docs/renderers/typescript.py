# -*- coding: utf-8 -*-

import re

from .base import BaseRenderer
from .schema import SchemaRenderer


# FIXME: test it!!!!!!!!!!!!!
class CommandsRenderer(BaseRenderer):

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns

    def render(self):

        base_index = super(CommandsRenderer, self).render()
        rendered = {}

        for path, conf in base_index.items():
            for method in ['post', 'get', 'put', 'delete']:
                try:
                    method_conf = conf[method]

                except KeyError:
                    pass

                else:
                    # -- take into account public commands
                    if method_conf['access'].is_private:
                        continue

                    # -- INTERFACES
                    schemas = {}
                    schemas['output'] = SchemaRenderer(
                        method_conf['output'].serializer).render().serialize()

                    if method_conf['input'].query_parser:
                        schemas['input_query'] = SchemaRenderer(
                            method_conf['input'].query_parser
                        ).render().serialize()

                    if method_conf['input'].body_parser:
                        schemas['input_body'] = SchemaRenderer(
                            method_conf['input'].body_parser
                        ).render().serialize()

                    rendered[method_conf['name']] = {
                        'method': method,
                        'path_conf': conf['path_conf'],
                        'meta': method_conf['meta'].serialize(),
                        'access': method_conf['access'].serialize(),
                        'schemas': schemas,
                        # FIXME: add tests cases for a given command!!!!
                    }

        return rendered

# class Enum:

#     def __init__(self, name, values):
#         self.name = name
#         self.values = list(values)
    # def remove_enums_duplicates(self):

    #     enums = {}
    #     duplicated_names = {}
    #     for enum in self.enums:
    #         name = self.serialize_enum_name(enum)

    #         # -- if enum of that name already exists
    #         if name in enums:
    #             # -- compare its value with the one currently processing
    #             if set(enums[name].values) != set(enum.values):
    #                 duplicated_names.setdefault(name, [])
    #                 duplicated_names[name].append(enum)

    #         else:
    #             enum.name = name
    #             enums[name] = enum

    #     for name, duplicated_enums in duplicated_names.items():
    #         for i, enum in enumerate(duplicated_enums):
    #             enum.name = '{name}{index}'.format(name=name, index=i + 1)
    #             enums[enum.name] = enum

    #     return list(enums.values())

    # def serialize_enum_name(self, enum):

    #     name = to_camelcase(enum.name)

    #     if self.type == SERIALIZER_TYPES.RESPONSE:
    #         return 'Response{}'.format(name)

    #     elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
    #         return 'RequestBody{}'.format(name)

    #     elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
    #         return 'RequestQuery{}'.format(name)


def to_camelcase(name):
    tokens = re.split(r'\_+', name)

    return ''.join([token.capitalize() for token in tokens])

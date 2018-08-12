# -*- coding: utf-8 -*-

from .utils import to_camelcase
from lily.base.utils import normalize_indentation


class Interface:

    class TYPES:  # noqa
        RESPONSE = 'RESPONSE'

        REQUEST_QUERY = 'REQUEST_QUERY'

        REQUEST_BODY = 'REQUEST_BODY'

    def __init__(self, command_name, type_, schema, uri, bulk_read_field=None):
        self.command_name = command_name
        self.type = type_
        self.schema = schema
        self.uri = uri
        self.enums = []
        self.bulk_read_field = bulk_read_field

    def is_empty(self):
        return self.schema is None or self.schema == {}

    def append_enum(self, field_name, values):

        index = 0
        new_enum = None
        for enum in self.enums:
            if enum.field_name == field_name and enum.values != set(values):
                index += 1

            elif enum.field_name == field_name and enum.values == set(values):
                new_enum = enum
                break

        if not new_enum:
            new_enum = Enum(
                field_name, values, self.name, index > 0 and index or None)
            self.enums.append(new_enum)

        return new_enum

    @property
    def name(self):
        if self.type == self.TYPES.RESPONSE:
            suffix = 'Response'

        elif self.type == self.TYPES.REQUEST_QUERY:
            suffix = 'Query'

        else:
            suffix = 'Body'

        return '{name}{suffix}'.format(
            name=to_camelcase(self.command_name),
            suffix=suffix)

    def render(self):

        if self.schema is None:
            return ''

        def optional(name, schema):
            return name not in schema['required'] and '?' or ''

        def to_type(name, schema, indent):
            if schema['type'] in ['integer', 'number']:
                return 'number'

            elif schema['type'] == 'string' and schema.get('enum'):
                enum = self.append_enum(name, schema['enum'])
                return enum.name

            elif schema['type'] == 'boolean':
                return 'boolean'

            elif schema['type'] == 'string':
                return 'string'

            elif schema['type'] == 'any':
                return 'any'

            elif schema['type'] == 'object':
                if 'properties' in schema:
                    return to_interface(
                        schema, indent=indent + 4, base_indent=indent)
                else:
                    return 'Object'

        def to_interface(schema, indent=4, base_indent=0):

            lines = []
            if schema['type'] == 'object':
                lines.append('{')
                names = sorted(schema['properties'].keys())

                for name in names:
                    sub_schema = schema['properties'][name]

                    if sub_schema['type'] == 'array':
                        value = to_type(name, sub_schema['items'], indent)
                        value += '[]'

                    else:
                        value = to_type(name, sub_schema, indent)

                    lines.append(
                        '{indent}{name}{optional}: {value};'.format(
                            indent=' ' * indent,
                            name=name,
                            optional=optional(name, schema),
                            value=value)
                    )

                lines.append(' ' * base_indent + '}')

            return '\n'.join(lines)

        blocks = [normalize_indentation('''
            /**
             * {self.uri}
             */
        ''', 0).format(self=self)]

        # -- treat differently Bulk Read Response interfaces in order to
        # -- allow one extra mapping in the domain service
        if self.bulk_read_field:
            field = list(self.schema['properties'].keys())[0]

            entity_schema = self.schema['properties'][field]['items']

            interface = normalize_indentation('''
                export interface {self.name}Entity {interface_content}

                export interface {self.name} {{
                    {self.bulk_read_field}: {self.name}Entity[];
                }}

                ''', 0).format(
                self=self,
                interface_content=to_interface(entity_schema))

        # -- deal with empty schema which might occur for the case of
        # -- responses that return only @event field
        elif not self.schema:
            interface = 'export interface {self.name} {{}}'.format(self=self)

        else:
            interface = normalize_indentation(
                'export interface {self.name} {interface_content}'.format(
                    self=self,
                    interface_content=to_interface(self.schema)), 0)

        if self.enums:
            blocks.extend([enum.render() for enum in self.enums])
            blocks.append(interface)

        else:
            blocks.append(interface)

        return '\n\n'.join(blocks)


class Enum:

    def __init__(self, field_name, values, interface_name, index=None):
        self.field_name = field_name
        self.interface_name = interface_name
        self.values = set(values)
        self.index = index

    def __eq__(self, other):
        return (
            self.field_name.lower() == other.field_name.lower() and
            self.interface_name.lower() == other.interface_name.lower() and
            self.values == other.values and
            self.index == other.index)

    @property
    def name(self):
        return '{interface_name}{field_name}{index}'.format(
            interface_name=self.interface_name,
            field_name=to_camelcase(self.field_name),
            index=(self.index is not None and self.index) or '')

    def render(self):
        return 'export enum {name} {{\n{fields}\n}}'.format(
            name=self.name,
            fields='\n'.join(
                ["    {v} = '{v}',".format(v=v) for v in sorted(self.values)]))

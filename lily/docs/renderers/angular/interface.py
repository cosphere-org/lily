
import re

from .utils import to_camelcase
from lily.base.utils import normalize_indentation
from lily import EventFactory


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

    def append_enum(self, name, values):

        new_enum = Enum(name, values)
        if new_enum not in self.enums:
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
            return '', []

        def optional(name, schema):
            return name not in schema.get('required', []) and '?' or ''

        def to_type(name, schema, indent):
            _type = schema.get('type')
            if _type in ['integer', 'number']:
                return 'number'

            elif _type == 'string' and schema.get('enum'):
                enum = self.append_enum(schema['enum_name'], schema['enum'])

                if schema.get('const_value'):
                    v = schema['const_value']
                    return f'{enum.name}.{enum.get_key_for_value(v)}'

                return enum.name

            elif _type == 'null':
                return 'null'

            elif _type == 'boolean':
                return 'boolean'

            elif _type == 'string':
                if 'const' in schema:
                    const = schema['const']
                    return f'"{const}"'

                return 'string'

            elif _type == 'any':
                return 'any'

            elif _type == 'object':
                if 'properties' in schema:
                    return to_interface(
                        schema, indent=indent + 4, base_indent=indent)
                else:
                    return 'any'

            return 'any'

        def to_interface(schema, indent=4, base_indent=0):

            lines = []

            if schema['type'] == 'object':
                lines.append('{')

                entity_type = schema.get('entity_type')
                if entity_type:
                    lines.append(
                        normalize_indentation(
                            """
                                '@type'?: '{entity_type}';
                                '@access'?: {{
                                    [name: string]: {{
                                        is_active: boolean;
                                        reason: string;
                                    }};
                                }};
                            """.format(entity_type=entity_type),
                            indent))

                names = sorted(schema['properties'].keys())

                for name in names:
                    sub_schema = schema['properties'][name]

                    if sub_schema.get('oneOf'):
                        values = []
                        for alt_schema in sub_schema.get('oneOf'):
                            values.append(to_type(name, alt_schema, indent))

                        value = ' | '.join(values)

                    elif (sub_schema.get('type') == 'array' and
                            sub_schema['items'].get('oneOf')):

                        values = []
                        for alt_schema in sub_schema['items']['oneOf']:
                            values.append(to_type(name, alt_schema, indent))

                        value = ' | '.join(values)
                        value = f'({value})[]'

                    elif sub_schema.get('type') == 'array':
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

            elif schema['type'] in ['integer', 'number']:
                lines.append('extends Number {}')

            elif schema['type'] in ['string', 'boolean']:
                lines.append(
                    'extends {} {{}}'.format(schema['type'].capitalize()))

            return '\n'.join(lines)

        blocks = [normalize_indentation('''
            /**
             * {self.uri}
             */
        ''', 0).format(self=self)]

        # -- treat differently Bulk Read Response interfaces in order to
        # -- allow one extra mapping in the domain service
        if self.bulk_read_field:
            try:
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

            # -- FIXME: this is a hack allowing one to provide very
            # -- forgiving interface when output schema is missing, when
            # -- for example one uses output from one service to provide
            # -- output for itself. This behaviour will be solved in the future
            # -- by usage of service client with exportable serializes
            except KeyError:

                interface = normalize_indentation('''
                    export interface {self.name}Entity extends Object {{}};

                    export interface {self.name} {{
                        {self.bulk_read_field}: {self.name}Entity[];
                    }}

                    ''', 0).format(self=self)

        # -- deal with empty schema which might occur for the case of
        # -- responses that return only @event field
        elif not self.schema:
            interface = 'export interface {self.name} {{}}'.format(self=self)

        else:
            interface = normalize_indentation(
                'export interface {self.name} {interface_content}'.format(
                    self=self,
                    interface_content=to_interface(self.schema)), 0)

        blocks.append(interface)

        return '\n\n'.join(blocks), self.enums


class Enum:

    def __init__(self, name, values, index=None):
        if not name:
            raise EventFactory.BrokenRequest(
                'ENUMS_WITHOUT_NAME_DETECTED',
                data={'name': name, 'values': values})

        self.name = to_camelcase(name)
        self.values = set(values)
        self.index = index

    def __eq__(self, other):
        return (
            self.name.lower() == other.name.lower() and
            self.values == other.values)

    def render(self):

        values = self.values
        value_pairs = []
        for v in sorted(values):

            if isinstance(v, int):
                value = v

            else:
                value = f"'{v}'"

            value_pairs.append((self.get_key_for_value(v), value))

        return 'export enum {name} {{\n{fields}\n}}'.format(
            name=self.name,
            fields='\n'.join([
                f"    {k} = {v}," for k, v in value_pairs]))

    def get_key_for_value(self, value):

        def transform_key(k):
            return re.sub(r'[^\w]+', '_', k).upper()

        if isinstance(value, int):
            key = f'VALUE_{value}'

        elif isinstance(value, str) and re.search(r'^\d+', value):
            key = f'VALUE_{value}'

        else:
            key = value

        return transform_key(key)

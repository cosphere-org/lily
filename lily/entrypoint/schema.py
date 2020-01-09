
from enum import Enum, unique
import inspect
import re
import os

from lily_assistant.config import Config

from lily.base import serializers, parsers
from lily.base.models import JSONSchemaValidator


class MissingReturnStatementError(Exception):
    """Raise when return value is not declared.

    When Method used for calculating dynamical serialization field is
    missing the return annotation.

    """


class MissingMethodForFieldError(Exception):
    """Raise when method does not exist.

    When Method used for calculating dynamical serialization field is
    missing.

    """


class MissingSchemaMappingError(Exception):
    """Raise when schema mapping is missing.

    When mapping between any type of a field in the Serializer and schema
    is missing.

    """


class ForbiddenFieldError(Exception):
    """Raise when schema field is forbidden."""


@unique
class SerializerType(Enum):

    RESPONSE = 'RESPONSE'

    REQUEST_QUERY = 'REQUEST_QUERY'

    REQUEST_BODY = 'REQUEST_BODY'

    REQUEST_HEADER = 'REQUEST_HEADER'


class SchemaRenderer:

    def __init__(self, serializer, parser_type=None):

        # -- figure out with which type of Serializer or Parser we're
        # -- dealing with
        if inspect.isclass(serializer):
            instance = serializer()

        else:
            instance = serializer

        if isinstance(instance, serializers.Serializer):
            self.type = SerializerType.RESPONSE.value

        elif (isinstance(instance, parsers.Parser) and
                parser_type == parsers.ParserTypeEnum.BODY.value):
            self.type = SerializerType.REQUEST_BODY.value

        elif (isinstance(instance, parsers.Parser) and
                parser_type == parsers.ParserTypeEnum.QUERY.value):
            self.type = SerializerType.REQUEST_QUERY.value

        else:
            self.type = None

        self.serializer = serializer

        # -- fill in the meta data
        self.meta = self.get_meta(serializer)

    def get_meta(self, serializer):
        path = inspect.getfile(serializer)
        path = path.replace(Config.get_project_path(), '')

        return {
            'first_line': inspect.getsourcelines(serializer)[1],
            'path': path,
        }

    def render(self):

        return self.serializer_to_schema(self.serializer)

    def serializer_to_schema(self, serializer):

        schema = Schema(
            self.type,
            self.meta,
            getattr(serializer, '_type', None))

        try:
            fields = serializer.get_fields()

        except TypeError:
            fields = serializer().get_fields()

        for name, field in fields.items():

            # -- list serializer
            if isinstance(field, serializers.ListSerializer):
                schema.add_array(
                    name=name,
                    required=field.child.required,
                    value=self.serializer_to_schema(
                        field.child.__class__()))

            # -- singleton nested serializer
            elif (
                    isinstance(field, serializers.Serializer) or
                    isinstance(field, parsers.Parser)):

                schema.add(
                    name=name,
                    required=field.required,
                    value=self.serializer_to_schema(field))

            # -- method serializer
            elif isinstance(field, serializers.SerializerMethodField):
                schema = self.method_field_to_schema(
                    serializer, name, field, schema)

            # -- normal field boolean field
            elif self.is_simple_field(field):
                value, enums = self.simple_field_to_schema(name, field)
                schema.add(
                    name=name,
                    required=field.required,
                    value=value)
                schema.enums.extend(enums)

            # -- list field
            elif isinstance(field, serializers.ListField):

                if self.is_simple_field(field.child):
                    value, enums = self.simple_field_to_schema(
                        name, field.child)
                    schema.add_array(
                        name=name,
                        required=field.required,
                        value=value)
                    schema.enums.extend(enums)

                else:
                    schema.add_array(
                        name=name,
                        required=field.required,
                        value=self.serializer_to_schema(field.child))

            # -- all not covered cases should raise an Error
            else:
                raise MissingSchemaMappingError(
                    '{serializer}.{name}'.format(
                        serializer=self.get_name(serializer),
                        name=name))

        return schema

    def method_field_to_schema(self, serializer, name, field, schema):

        try:
            method = getattr(serializer, 'get_{}'.format(name))
            return_value = method.__annotations__['return']

        except KeyError:
            raise MissingReturnStatementError(
                'Missing Return Statement for Serializer {0} '
                'and method {1}'.format(self.get_name(serializer), method))

        except AttributeError:
            raise MissingMethodForFieldError(
                'Missing Method Statement for Serializer {0} '
                'and field {1}'.format(self.get_name(serializer), name))

        else:
            if isinstance(return_value, list):
                item_type = return_value[0]

                # -- if it's already a schema
                if isinstance(item_type, dict):
                    schema.add_array(
                        name=name,
                        required=True,
                        value=item_type)

                elif isinstance(item_type(), serializers.Serializer):
                    schema.add_array(
                        name=name,
                        required=True,
                        value=self.serializer_to_schema(item_type))

                else:
                    schema.add_array(
                        name=name,
                        required=True,
                        value=self.native_type_to_schema(item_type))

            # -- if it's already a schema
            elif isinstance(return_value, dict):
                schema.add(
                    name=name,
                    required=True,
                    value=return_value)

            elif isinstance(return_value(), serializers.Serializer):
                schema.add(
                    name=name,
                    required=True,
                    value=self.serializer_to_schema(return_value))

            else:
                schema.add(
                    name=name,
                    required=True,
                    value=self.native_type_to_schema(return_value))

        return schema

    def get_name(self, obj):
        try:
            return obj.__name__

        except AttributeError:
            return obj.__class__.__name__

    def is_simple_field(self, field):
        return isinstance(
            field,
            (
                serializers.BooleanField,
                serializers.CharField,
                serializers.ChoiceField,
                serializers.DateField,
                serializers.DateTimeField,
                serializers.DecimalField,
                serializers.DictField,
                serializers.EmailField,
                serializers.FloatField,
                serializers.IntegerField,
                serializers.JSONField,
                serializers.JSONSchemaField,
                serializers.URLField,
                serializers.ReadOnlyField,
                serializers.UUIDField,
            ))

    def simple_field_to_schema(self, name, field):
        enums = []
        out = None

        def is_field(_types):
            return isinstance(field, _types)

        if is_field(serializers.BooleanField):
            out = {
                'type': 'boolean',
            }

        # FIXME: figure out how to fetch the type hidden behind ReadOnly
        # Field!!!!!!!!!!!!!
        elif is_field(serializers.ReadOnlyField):
            out = {
                'type': 'any',
            }

        # -- must be before CharField
        elif is_field(serializers.EmailField):
            out = {
                'type': 'string',
                'format': 'email',
            }

        # -- must be before CharField
        elif is_field(serializers.URLField):
            out = {
                'type': 'string',
                'format': 'uri',
            }

        elif is_field(serializers.DateField):
            out = {
                'type': 'string',
                'format': 'date',
            }

        elif is_field(serializers.DateTimeField):
            out = {
                'type': 'string',
                'format': 'date-time',
            }

        elif is_field(serializers.UUIDField):
            out = {
                'type': 'string',
            }

        elif is_field(serializers.CharField):
            field_schema = {
                'type': 'string',
            }

            if field.min_length:
                field_schema['minLength'] = field.min_length

            if field.max_length:
                field_schema['maxLength'] = field.max_length

            out = field_schema

        elif is_field(serializers.IntegerField):
            field_schema = {
                'type': 'integer',
            }

            if field.min_value:
                field_schema['minimum'] = field.min_value

            if field.max_value:
                field_schema['maximum'] = field.max_value

            out = field_schema

        elif is_field(serializers.DecimalField):
            out = {
                'type': 'string',
            }

        elif is_field(serializers.FloatField):
            field_schema = {
                'type': 'number',
            }

            if field.min_value:
                field_schema['minimum'] = field.min_value

            if field.max_value:
                field_schema['maximum'] = field.max_value

            out = field_schema

        # -- choice fields are FORBIDDEN since they lead to ambiguous Enums
        # -- on the client side
        elif (
                is_field(serializers.ChoiceField) and
                not is_field(serializers.EnumChoiceField)):
            raise ForbiddenFieldError(
                f'{name} uses ChoiceField which is forbidden since it leads '
                f'to ambiguous client side Enums. Please use '
                f'`EnumChoiceField` instead')

        elif is_field(serializers.EnumChoiceField):
            choices = list(field.choices.keys())
            choice_type = type(choices[0])
            has_same_type = all([isinstance(c, choice_type) for c in choices])

            if has_same_type and isinstance(choices[0], int):
                schema_type = 'integer'

            else:
                schema_type = 'string'

            out = {
                'type': schema_type,
                'enum_name': field.enum_name,
                'enum': sorted(choices),
            }
            enums.append(out)

        elif is_field(serializers.DictField):
            out = {
                'type': 'object',
            }

        elif is_field((serializers.JSONField, serializers.JSONSchemaField)):

            out = {
                'type': 'any',
            }

            # -- search for the 1st JSONSchemaValidator validator
            # -- the should be always at most one.
            for validator in field.validators:
                if isinstance(validator, JSONSchemaValidator):
                    out = validator.schema
                    if 'schemas' in out:
                        out = {
                            'oneOf': out['oneOf']
                        }

        return out, enums

    def native_type_to_schema(self, _type):

        if _type in [int, float]:
            return {
                'type': 'number',
            }

        elif _type == str:
            return {
                'type': 'string',
            }

        elif _type == bool:
            return {
                'type': 'boolean',
            }


class ArrayValue:

    def __init__(self, value):
        self.value = value


class Schema:

    def __init__(self, type_, meta, entity_type=None):
        self.type = type_
        self.meta = meta
        self.schema = self.get_empty_schema()

        if entity_type:
            self.schema['entity_type'] = entity_type

        self.enums = []

    def is_empty(self):
        return self.schema == self.get_empty_schema()

    def get_empty_schema(self):
        return {
            'type': 'object',
            'required': [],
            'properties': {},
        }

    #
    # Adding Values to the Root Schema
    #
    def add_array(self, name, value, required=True):
        if isinstance(value, Schema):
            self.enums.extend(value.enums)

        self.add(name, ArrayValue(value), required)

    def add(self, name, value, required=True):
        if isinstance(value, Schema):
            self.enums.extend(value.enums)

        self.schema['properties'][name] = value
        if required:
            self.schema['required'].append(name)

    #
    # Representation
    #
    def serialize(self):

        def serialize(d):

            entity_type = d.get('entity_type', None)

            o = {
                'type': d['type'],
                'required': d['required'],
                'properties': {},
            }
            if entity_type:
                o['entity_type'] = entity_type

            p = o['properties']

            for k, v in d['properties'].items():
                if isinstance(v, Schema):
                    p[k] = serialize(v.schema)

                elif isinstance(v, ArrayValue):
                    if isinstance(v.value, Schema):
                        p[k] = {
                            'type': 'array',
                            'items': serialize(v.value.schema),
                        }

                    else:
                        p[k] = {
                            'type': 'array',
                            'items': v.value,
                        }

                else:
                    p[k] = v

            return o

        if self.is_empty():
            schema = {}

        else:
            schema = serialize(self.schema)

        return {
            'uri': self.get_repository_uri(),
            'schema': schema,
        }

    def get_repository_uri(self):
        config = Config()

        if 'bitbucket' in config.repository:
            return os.path.join(
                config.repository,
                'src',
                config.last_commit_hash,
                re.sub(r'^/', '', self.meta['path']),
                '#lines-{}'.format(self.meta['first_line']))

        elif 'github':
            return os.path.join(
                config.repository,
                'blob',
                config.last_commit_hash,
                re.sub(r'^/', '', self.meta['path']),
                '#L{}'.format(self.meta['first_line']))

# -*- coding: utf-8 -*-

import inspect
import re
import os

from django.conf import settings

from lily.base import serializers, parsers, config


class MissingReturnStatementError(Exception):
    """
    When Method used for calculating dynamical serialization field is
    missing the return annotation.

    """


class MissingMethodForFieldError(Exception):
    """
    When Method used for calculating dynamical serialization field is
    missing.

    """


class MissingInterfaceMappingError(Exception):
    """
    When mapping between any type of a field in the Serializer and schema
    is missing.

    """


class SERIALIZER_TYPES:  # noqa
    RESPONSE = 'RESPONSE'

    REQUEST_QUERY = 'REQUEST_QUERY'

    REQUEST_BODY = 'REQUEST_BODY'

    REQUEST_HEADER = 'REQUEST_HEADER'


class SchemaRenderer:

    def __init__(self, serializer):

        # -- figure out with which type of Serializer or Parser we're
        # -- dealing with
        if inspect.isclass(serializer):
            instance = serializer()

        else:
            instance = serializer

        if isinstance(instance, serializers.Serializer):
            self.type = SERIALIZER_TYPES.RESPONSE

        elif isinstance(instance, parsers.BodyParser):
            self.type = SERIALIZER_TYPES.REQUEST_BODY

        elif isinstance(instance, parsers.QueryParser):
            self.type = SERIALIZER_TYPES.REQUEST_QUERY

        self.serializer = serializer

        # -- fill in the meta data
        self.meta = self.get_meta(serializer)

    def get_meta(self, serializer):
        path = inspect.getfile(serializer)
        path = path.replace(settings.LILY_PROJECT_BASE, '')

        return {
            'first_line': inspect.getsourcelines(serializer)[1],
            'path': path,
        }

    def render(self):
        return self.serializer_to_schema(self.serializer)

    def serializer_to_schema(self, serializer):
        schema = Schema(self.type, self.meta)

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
                    isinstance(field, parsers.BodyParser) or
                    isinstance(field, parsers.QueryParser)):

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
                schema.add(
                    name=name,
                    required=field.required,
                    value=self.simple_field_to_schema(name, field))

            # -- list field
            elif isinstance(field, serializers.ListField):

                if self.is_simple_field(field.child):
                    schema.add_array(
                        name=name,
                        required=field.child.required,
                        value=self.simple_field_to_schema(
                            name, field.child))

                else:
                    schema.add_array(
                        name=name,
                        required=field.child.required,
                        value=self.serializer_to_schema(field.child))

            # -- all not covered cases should raise an Error
            else:
                # FIXME: test it!!!!!
                raise MissingInterfaceMappingError(
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

                if isinstance(item_type(), serializers.Serializer):
                    schema.add_array(
                        name=name,
                        required=True,
                        value=self.serializer_to_schema(item_type))

                else:
                    schema.add_array(
                        name=name,
                        required=True,
                        value=self.native_type_to_schema(item_type))

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
                serializers.URLField,
                serializers.ReadOnlyField,
            ))

    def simple_field_to_schema(self, name, field):

        is_field = lambda _types: isinstance(field, _types)

        if is_field((serializers.BooleanField,)):
            return {
                'type': 'boolean',
            }

        # FIXME: figure out how to fetch the type hidden behind ReadOnly
        # Field!!!!!!!!!!!!!
        elif is_field((serializers.ReadOnlyField,)):
            return {
                'type': 'any',
            }

        # -- must be before CharField
        elif is_field(serializers.EmailField):
            return {
                'type': 'string',
                'format': 'email',
            }

        # -- must be before CharField
        elif is_field(serializers.URLField):
            return {
                'type': 'string',
                'format': 'uri',
            }

        elif is_field(serializers.DateField):
            return {
                'type': 'string',
                'format': 'date',
            }

        elif is_field(serializers.DateTimeField):
            return {
                'type': 'string',
                'format': 'date-time',
            }

        elif is_field(serializers.CharField):
            field_schema = {
                'type': 'string',
            }

            if field.min_length:
                field_schema['minLength'] = field.min_length

            if field.max_length:
                field_schema['maxLength'] = field.max_length

            return field_schema

        elif is_field(serializers.IntegerField):
            field_schema = {
                'type': 'integer',
            }

            if field.min_value:
                field_schema['minimum'] = field.min_value

            if field.max_value:
                field_schema['maximum'] = field.max_value

            return field_schema

        elif is_field(serializers.DecimalField):
            return {
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

            return field_schema

        elif is_field(serializers.ChoiceField):
            # FIXME: how to solve problems of enums!!!!
            # !!!!!!!!! enums should be solved when fetched by the
            # client generator!!!!
            return {
                'type': 'string',
                'enum': sorted(field.choices.keys()),
            }

        elif is_field((
            serializers.DictField,
            serializers.JSONField,
        )):
            return {
                'type': 'object',
            }

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

    def __init__(self, type_, meta):
        self.type = type_
        self.meta = meta
        self.schema = self.get_empty_schema()
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

            o = {
                'type': d['type'],
                'required': d['required'],
                'properties': {},
            }
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
            'name': self.serialize_name(),
            'schema': schema,
        }

    def serialize_name(self):
        if self.type == SERIALIZER_TYPES.RESPONSE:
            return 'Response'

        elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
            return 'RequestBody'

        elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
            return 'RequestQuery'

    def get_repository_uri(self):
        """ Bitbucket specific repository uri generator.

        TODO: Make it to work for github too.

        """

        return os.path.join(
            config.repository,
            'src',
            config.last_commit_hash,
            re.sub(r'^/', '', self.meta['path']),
            '#lines-{}'.format(self.meta['first_line']))

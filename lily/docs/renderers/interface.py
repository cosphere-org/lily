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
    When mapping between any type of a field in the Serializer and interface
    is missing.

    """


class SERIALIZER_TYPES:  # noqa
    RESPONSE = 'RESPONSE'

    REQUEST_QUERY = 'REQUEST_QUERY'

    REQUEST_BODY = 'REQUEST_BODY'

    REQUEST_HEADER = 'REQUEST_HEADER'


class InterfaceRenderer:

    def __init__(self, serializer):

        # -- figure out with which type of Serializer or Parser we're
        # -- dealing with
        if serializers.Serializer in serializer.__mro__:
            self.type = SERIALIZER_TYPES.RESPONSE

        elif parsers.BodyParser in serializer.__mro__:
            self.type = SERIALIZER_TYPES.REQUEST_BODY

        elif parsers.QueryParser in serializer.__mro__:
            self.type = SERIALIZER_TYPES.REQUEST_QUERY

        # -- fill meta data
        path = inspect.getfile(serializer)
        path = path.replace(settings.LILY_PROJECT_BASE, '')
        self.meta = {
            'first_line': inspect.getsourcelines(serializer)[1],
            'path': path,
        }

        self.serializer = serializer

    def render(self):
        return self.serializer_to_interface(self.serializer)

    def serializer_to_interface(self, serializer):
        interface = Interface(self.type, self.meta)

        try:
            fields = serializer.get_fields()

        except TypeError:
            fields = serializer().get_fields()

        for name, field in fields.items():

            # -- list serializer
            if isinstance(field, serializers.ListSerializer):
                interface.add_array(
                    name=name,
                    required=field.child.required,
                    value=self.serializer_to_interface(
                        field.child.__class__()))

            # -- singleton nested serializer
            elif (
                    isinstance(field, serializers.Serializer) or
                    isinstance(field, parsers.BodyParser) or
                    isinstance(field, parsers.QueryParser)):

                interface.add(
                    name=name,
                    required=field.required,
                    value=self.serializer_to_interface(field))

            # -- method serializer
            elif isinstance(field, serializers.SerializerMethodField):
                interface = self.method_field_to_interface(
                    serializer, name, field, interface)

            # -- normal field boolean field
            elif self.is_simple_field(field):
                interface.add(
                    name=name,
                    required=field.required,
                    value=self.simple_field_to_interface(name, field))

            # -- list field
            elif isinstance(field, serializers.ListField):

                if self.is_simple_field(field.child):
                    interface.add_array(
                        name=name,
                        required=field.child.required,
                        value=self.simple_field_to_interface(
                            name, field.child))

                else:
                    interface.add_array(
                        name=name,
                        required=field.child.required,
                        value=self.serializer_to_interface(field.child))

            # -- all not covered cases should raise an Error
            else:
                raise MissingInterfaceMappingError(
                    '{serializer}.{name}'.format(
                        serializer=serializer.__name__,
                        name=name))

        return interface

    def method_field_to_interface(self, serializer, name, field, interface):

        try:
            method = getattr(serializer, 'get_{}'.format(name))
            return_value = method.__annotations__['return']

        except KeyError:
            raise MissingReturnStatementError()

        except AttributeError:
            raise MissingMethodForFieldError()

        else:
            if isinstance(return_value, list):
                item_type = return_value[0]

                if isinstance(item_type(), serializers.Serializer):
                    interface.add_array(
                        name=name,
                        required=True,
                        value=self.serializer_to_interface(item_type))

                else:
                    interface.add_array(
                        name=name,
                        required=True,
                        value=self.native_type_to_interface(item_type))

            elif isinstance(return_value(), serializers.Serializer):
                interface.add(
                    name=name,
                    required=True,
                    value=self.serializer_to_interface(return_value))

            else:
                interface.add(
                    name=name,
                    required=True,
                    value=self.native_type_to_interface(return_value))

        return interface

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
            ))

    def simple_field_to_interface(self, name, field):

        is_field = lambda _types: isinstance(field, _types)

        if is_field((serializers.BooleanField,)):
            return 'boolean'

        elif is_field((
            serializers.EmailField,
            serializers.URLField,
            serializers.DateField,
            serializers.DateTimeField,
            serializers.CharField,
            serializers.DecimalField,
        )):
            return 'string'

        elif is_field((
            serializers.IntegerField,
            serializers.FloatField,
        )):
            return 'number'

        elif is_field(serializers.ChoiceField):
            return Enum(name, field.choices.keys())

        elif is_field((
            serializers.DictField,
            serializers.JSONField,
        )):
            return 'object'

    def native_type_to_interface(self, _type):

        if _type in [int, float]:
            return 'number'

        elif _type == str:
            return 'string'

        elif _type == bool:
            return 'boolean'


class ArrayValue:

    def __init__(self, value):
        self.value = value


class Enum:

    def __init__(self, name, values):
        self.name = name
        self.values = list(values)


class Interface:

    def __init__(self, type_, meta):
        self.type = type_
        self.meta = meta
        self.interface = {}
        self.enums = []

    #
    # Adding Values to the Root Interface
    #
    def add_array(self, name, value, required=True):
        self.add(name, ArrayValue(value), required)

    def add(self, name, value, required=True):
        if isinstance(value, Enum):
            self.enums.append(value)

        if isinstance(value, Interface):
            self.enums.extend(value.enums)

        self.interface[self.get_name(name, required)] = value

    def get_name(self, name, required):
        return '{name}{optional}'.format(
            name=name, optional=(not required and '?') or '')

    #
    # Representation
    #
    def serialize(self):

        enums = self.remove_enums_duplicates()

        def serialize(d):

            o = {}
            for k, v in d.items():
                if isinstance(v, Enum):
                    o[k] = v.name

                elif isinstance(v, Interface):
                    o[k] = serialize(v.interface)

                elif isinstance(v, ArrayValue):
                    # FIXME: test it!!!!!!!!!
                    if isinstance(v.value, Enum):
                        o[k] = {
                            '__type': 'array',
                            '__items': v.value.name,
                        }

                    elif isinstance(v.value, Interface):
                        o[k] = {
                            '__type': 'array',
                            '__items': serialize(v.value.interface),
                        }

                    else:
                        o[k] = {
                            '__type': 'array',
                            '__items': v.value,
                        }

                else:
                    o[k] = v

            return o

        return {
            'interface': {
                'uri': self.get_repository_uri(),
                'name': self.serialize_name(),
                'interface': serialize(self.interface),
            },
            'enums': {enum.name: enum.values for enum in enums},
        }

    def serialize_name(self):
        if self.type == SERIALIZER_TYPES.RESPONSE:
            return 'Response'

        elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
            return 'RequestBody'

        elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
            return 'RequestQuery'

    def get_repository_uri(self):
        return os.path.join(
            config.repository,
            'src',
            config.last_commit_hash,
            re.sub(r'^/', '', self.meta['path']),
            '#lines-{}'.format(self.meta['first_line']))

    def remove_enums_duplicates(self):

        enums = {}
        duplicated_names = {}
        for enum in self.enums:
            name = self.serialize_enum_name(enum)

            # -- if enum of that name already exists
            if name in enums:
                # -- compare its value with the one currently processing
                existing = enums[name]

                if set(existing) != set(enum.values):
                    duplicated_names.setdefault(name, [])
                    duplicated_names[name].append(enum)

            else:
                enum.name = name
                enums[name] = enum.values

        for name, duplicated_enums in duplicated_names.items():
            for i, enum in enumerate(duplicated_enums):
                enum.name = '{name}{index}'.format(name=name, index=i + 1)
                enums[enum.name] = enum.values

        return self.enums

    def serialize_enum_name(self, enum):

        name = underscore_to_camel(enum.name)

        if self.type == SERIALIZER_TYPES.RESPONSE:
            return 'Response{}'.format(name)

        elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
            return 'RequestBody{}'.format(name)

        elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
            return 'RequestQuery{}'.format(name)


def underscore_to_camel(name):
    tokens = re.split(r'\_+', name)

    return ''.join([token.capitalize() for token in tokens])

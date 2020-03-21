
import re
import os
from copy import copy, deepcopy

from rest_framework import serializers as drf_serializers
from rest_framework.serializers import (  # noqa
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    DictField,
    EmailField,
    FloatField,
    IntegerField,
    JSONField,
    ListField,
    ListSerializer,
    SerializerMethodField,
    URLField,
    UUIDField,
    NullBooleanField,
    ValidationError,
    ReadOnlyField,
)

from .events import EventFactory


BASE_DIR = os.path.dirname(__file__)


COMMANDS_CONF = {}


class MissingTypeError(Exception):
    """Could not find `_type` attribute.

    When Serializer is missing the semantic `_type` denoting a type which
    Entity a given Serializer represents.

    """


class MissingRequiredArgumentsException(Exception):
    pass


class EnumChoiceField(ChoiceField):

    def __init__(self, *args, enum_name=None, enum=None, **kwargs):

        if enum_name:
            self.enum_name = enum_name

        if enum:
            self.enum_name = enum.__name__
            kwargs['choices'] = [e.value for e in enum]

        if not (enum_name or enum):
            raise MissingRequiredArgumentsException(
                'either `enum_name` or `enum` must be provided')

        super(EnumChoiceField, self).__init__(*args, **kwargs)


class Serializer(drf_serializers.Serializer, EventFactory):

    def __init__(self, *args, fields_subset=None, **kwargs):
        self._fields_subset = fields_subset
        super(Serializer, self).__init__(*args, **kwargs)

    def render_access(self, instance):

        try:
            out_access = {}
            for cmd, is_active in self.get_access(instance):
                if isinstance(cmd, str):
                    name = cmd

                else:
                    name = cmd.command_conf['name']

                out_access[name] = is_active

            return out_access

        except AttributeError:
            pass

        return {}

    def to_internal_value(self, data):

        try:
            transformed = deepcopy(data)
            for field_name, value in data.items():
                if field_name.startswith('@'):
                    new_field_name = re.sub(r'^@', 'at__', field_name)
                    transformed[new_field_name] = value
                    del transformed[field_name]

            return super(Serializer, self).to_internal_value(transformed)

        except AttributeError:
            # -- HACK: which allows me to return instances of models inside
            # -- normal dictionary
            return data

    def to_representation(self, instance):

        if self._fields_subset:
            body = {
                f: getattr(instance, f)
                for f in self._fields_subset
            }

        # -- when dealing with DICT
        elif isinstance(instance, dict):
            transformed = copy(instance)
            for field_name, value in instance.items():
                if field_name.startswith('@'):
                    new_field_name = re.sub(r'^@', 'at__', field_name)
                    transformed[new_field_name] = value
                    del transformed[field_name]

            body = super(Serializer, self).to_representation(transformed)

        # -- when dealing normal instance
        else:
            body = super(Serializer, self).to_representation(instance)

        # -- transform `at__` to `@`
        original = copy(body)
        for field_name, value in original.items():
            if field_name.startswith('at__'):
                new_field_name = re.sub(r'^at__', '@', field_name)
                body[new_field_name] = value
                del body[field_name]

        # --
        # -- attach type meta info
        # --
        # -- for `AbstractSerializer` do not attach any extra data they are
        # -- here only for storing SubEntities without having their own
        # -- interpretation
        if isinstance(self, AbstractSerializer):
            return body

        try:
            body['@type'] = self._type

        except AttributeError:
            raise MissingTypeError(
                'Each Serializer must have `type` specified which informs '
                'the client about the semantic type a result of the '
                'Serializer represents')

        access = self.render_access(instance)
        if access:
            body['@access'] = access

        return body


class AbstractSerializer(Serializer):
    """Store abstract entities.

    Designed for storing only abstract entities without having it's
    own meaning.

    """


class ModelSerializer(drf_serializers.ModelSerializer, Serializer):

    serializer_choice_field = EnumChoiceField

    def build_standard_field(self, field_name, model_field):

        from . import models  # noqa - avoid circular dependency

        field_class, field_kwargs = super(
            ModelSerializer, self).build_standard_field(
                field_name, model_field)

        if isinstance(model_field, models.EnumChoiceField):
            field_kwargs['enum_name'] = model_field.enum_name
            field_class = EnumChoiceField

        return field_class, field_kwargs


class EmptySerializer(Serializer):

    _type = 'empty'


class ObjectSerializer(Serializer):

    _type = 'object'

    def to_internal_value(self, data):

        return data

    def to_representation(self, data):

        data['@type'] = self._type

        return data


class CommandSerializer(Serializer):

    _type = 'command'

    name = CharField()

    method = ChoiceField(choices=('post', 'get', 'delete', 'put'))

    uri = URLField()

    body = DictField(required=False)

    query = DictField(required=False)

    result = DictField(required=False)


class JSONSchemaField(JSONField):
    def __init__(self, *args, **kwargs):
        from .models import JSONSchemaValidator

        class JSONSchemaValidatorSerializer(JSONSchemaValidator):

            validation_error_cls = ValidationError

        try:
            schema = kwargs.pop('schema')

        except KeyError:
            schema = {}

        super(JSONSchemaField, self).__init__(*args, **kwargs)
        self.validators.insert(
            0, JSONSchemaValidatorSerializer(schema=schema))


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


class Serializer(drf_serializers.Serializer, EventFactory):

    def __init__(self, *args, fields_subset=None, **kwargs):
        self._fields_subset = fields_subset
        super(Serializer, self).__init__(*args, **kwargs)

    def render_commands(self, instance):

        try:
            out_commands = {}
            for cmd, is_active in self.get_commands(instance):
                name = cmd.command_conf['name']

                out_commands[name] = {
                    'is_active': is_active,
                    'reason': f'REASON.ACCESS.{name}',
                }

            return out_commands

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
        try:
            body['@type'] = self._type

        except AttributeError:
            raise MissingTypeError(
                'Each Serializer must have `type` specified which informs '
                'the client about the semantic type a result of the '
                'Serializer represents')

        commands = self.render_commands(instance)
        if commands:
            body['@commands'] = commands

        return body


class ModelSerializer(drf_serializers.ModelSerializer, Serializer):
    pass


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

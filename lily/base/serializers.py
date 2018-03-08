# -*- coding: utf-8 -*-

import json
import re
import os
from copy import deepcopy
import logging

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
    ValidationError,
)

from .events import EventFactory


logger = logging.getLogger()


event = EventFactory(logger)


# FIXME: this will normally be read from the static conf file available
# somewhere -> maybe each service can upload newest conf file on
# deployment to S3???
# -- this can be read from the ENV variables!!!
# FIXME: add the file from which the conf will be fetched

BASE_DIR = os.path.dirname(__file__)

COMMANDS_CONF = json.loads(
    open(os.path.join(BASE_DIR, '../docs/commands_conf.json')).read())


class MissingTypeError(Exception):
    """
    When Serializer is missing the semantic `_type` denoting a type which
    Entity a given Serializer represents.

    """


class Serializer(drf_serializers.Serializer):

    def __init__(self, *args, fields_subset=None, **kwargs):
        self._fields_subset = fields_subset
        super(Serializer, self).__init__(*args, **kwargs)

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

        else:
            body = super(Serializer, self).to_representation(instance)

        # -- transform `at__` to `@`
        original = deepcopy(body)
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

        # --
        # -- attach command links
        # --
        try:
            request = self.context['request']
            command_name = self.context['command_name']

        # -- rendering of command links is optional and sometimes if someone
        # -- just wants to simply serialize some instance without knowing
        # -- the request or command name he can freely do this
        except (KeyError, AttributeError):
            request = None
            command_name = None

        try:
            if request and command_name:
                resolved_command_links = {}
                for cl in self._command_links:
                    resolved = cl.resolve(
                        request=request,
                        response=body,
                        _type=getattr(self, '_type'))
                    if resolved:
                        resolved_command_links[cl.name] = resolved

                if resolved_command_links:
                    # FIXME: maybe one could figure out some way to making
                    # the precomputation here
                    # -- extend any command which could be added inline
                    body['@commands'] = dict(
                        body.get('@commands', {}), **resolved_command_links)

        except AttributeError:
            pass

        return body


class ModelSerializer(drf_serializers.ModelSerializer, Serializer):
    pass


class EmptySerializer(Serializer):

    _type = 'empty'


class CommandSerializer(Serializer):

    _type = 'command'

    name = CharField()

    method = ChoiceField(choices=('post', 'get', 'delete', 'put'))

    uri = URLField()

    body = DictField(required=False)

    query = DictField(required=False)

    result = DictField(required=False)


class CommandLink:

    def __init__(self, name, parameters=None, description=None):
        self.name = name
        self.parameters = parameters or {}
        self.description = description

    def resolve(self, request, response, _type):
        try:
            command_conf = COMMANDS_CONF[self.name]

        except KeyError:
            return {}

        else:
            method = command_conf['method']

            # -- access_list is added by the Authorizer if at this stage
            # -- one cannot see it that means that Authorizer was not called
            # -- before this code was executed
            access_list = command_conf['access_list']
            service_base_uri = command_conf['service_base_uri']
            path_conf = command_conf['path_conf']
            path, parameters_conf = path_conf['path'], path_conf['parameters']
            body = command_conf.get('body')
            query = command_conf.get('query')

        # -- only authorized users can view commands giving client extra
        # -- information about what which user can see / or do
        if access_list and request.account_type not in access_list:
            return {}

        resolved_parameters = self.resolve_parameters(request, response, _type)

        # -- report an event but without raising it since detecting a
        # -- broken link is not important enough to break the whole response
        required_parameters = set([p['name'] for p in parameters_conf])

        if not required_parameters.issubset(set(resolved_parameters.keys())):
            event.Warning(
                event='MISSING_COMMAND_LINK_PARAMS_DETECTED',
                context=request,
                data={'from': request.command_name, 'to': self.name},
                is_critical=True)

        else:
            resolved = {
                'name': self.name,
                'method': method,
                'uri': '{base}{path}'.format(
                    base=service_base_uri,
                    path=path.format(**resolved_parameters)),
            }

            if body:
                resolved['body'] = body

            if query:
                resolved['query'] = query

            return resolved

    def resolve_pre_computed(
            self,
            request,
            response,
            _type,
            body_values=None,
            query_values=None):

        resolved = self.resolve(request, response, _type)

        def inject_values(values, field):
            for path, value in values.items():
                path = path.split('.')
                current = resolved[field]
                for path_step in path:
                    current = current[path_step]

                current['@value'] = value

        if body_values:
            inject_values(body_values, 'body')

        if query_values:
            inject_values(query_values, 'query')

        return resolved

    def resolve_with_result(self, request, response, _type, result):
        resolved = self.resolve(request, response, _type)
        resolved['result'] = result

        return resolved

    def resolve_parameters(self, request, response, _type=None):

        resolved = {}
        for name, pattern in self.parameters.items():
            parsed = self.parse_parameter_pattern(pattern)
            entity, prop, selector = (
                parsed['entity'], parsed['prop'], parsed['selector'])

            # -- RESPONSE
            if entity == 'response' and prop == 'body':
                value = response
                try:
                    for item in selector:
                        value = value[item]

                except KeyError:
                    pass

                else:
                    resolved[name] = value

            # -- REQUEST
            elif entity == 'request' and prop == 'header':
                header_name = 'HTTP_X_CS_{}'.format(selector.upper())
                resolved[name] = request.META[header_name]

        # -- one extends the resolved parameters by all values passed to the
        # -- response.
        # -- attach to the cloned body the more naturally sounding id
        # -- name e.g. if type is `client` than we attach `client_id`
        extended_resolved = deepcopy(response)
        try:
            if _type:
                natural_id = '{type}_id'.format(type=_type)
                extended_resolved[natural_id] = extended_resolved['id']

        except KeyError:
            pass

        extended_resolved.update(resolved)

        return extended_resolved

    def parse_parameter_pattern(self, pattern):
        re_pattern = re.compile(
            r'\$(?P<entity>request|response)'
            r'\.(?P<prop>path|body|header)'
            r'(?P<selector>(\#\/(\w+\/?)+)|\.\w+)'
        )

        parsed = re_pattern.search(pattern)

        if parsed:
            parsed = parsed.groupdict()

            if parsed['prop'] == 'body':
                parsed['selector'] = (
                    parsed['selector'].replace('#/', '').split('/'))

            else:
                parsed['selector'] = parsed['selector'].replace('.', '')

            return parsed

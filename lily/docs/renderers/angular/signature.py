# -*- coding: utf-8 -*-

import re

from .utils import to_camelcase


class Signature:

    def __init__(
            self,
            path,
            path_parameters,
            request_query=None,
            request_body=None):
        self.path = path
        self.path_parameters = path_parameters
        self.request_query = request_query
        self.request_body = request_body

    @property
    def input(self):

        def to_arg(parameter):
            if parameter['type'] == int:
                type_ = 'number'

            elif parameter['type'] == str:
                type_ = 'string'

            else:
                type_ = 'any'

            return '{arg}: {type}'.format(
                arg=to_camelcase(parameter['name'], first_lower=True),
                type=type_)

        input_signature = []
        # -- path parameters
        if self.path_parameters:
            input_signature.append(
                ', '.join([to_arg(p) for p in self.path_parameters]))

        # -- query
        if self.request_query:
            input_signature.append(
                'params: {}'.format(self.request_query.name))

        # -- body
        if self.request_body:
            input_signature.append(
                'body: {}'.format(self.request_body.name))

        return ', '.join(input_signature)

    @property
    def call_args(self):

        call_args_signature = []

        # -- path parameters
        path = re.sub(
            '\{(?P<parameter>[\w\_]+)\}',
            lambda x: '${{{}}}'.format(
                to_camelcase(x.groupdict()['parameter'], first_lower=True)),
            self.path)

        if self.path_parameters:
            call_args_signature.append('`{}`'.format(path))

        else:
            call_args_signature.append("'{}'".format(path))

        # -- query
        if self.request_query:
            call_args_signature.append('{ params }')

        # -- body
        if self.request_body:
            call_args_signature.append('body')

        return ', '.join(call_args_signature)

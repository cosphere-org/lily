
import re

from .utils import to_camelcase


class Signature:

    def __init__(
            self,
            method,
            path,
            path_parameters,
            authorization_required=True,
            request_query=None,
            request_body=None,
            bulk_read_field=None):
        self.method = method
        self.path = path
        self.path_parameters = path_parameters
        self.authorization_required = authorization_required
        self.request_query = request_query
        self.request_body = request_body
        self.bulk_read_field = bulk_read_field

    @property
    def input(self):

        input_signature = []
        # -- path parameters
        if self.path_parameters:
            input_signature.append(
                ', '.join([self.to_arg(p) for p in self.path_parameters]))

        # -- query
        if not self.request_query.is_empty():
            input_signature.append(
                'params: X.{}'.format(self.request_query.name))

        # -- body
        if not self.request_body.is_empty():
            input_signature.append(
                'body: X.{}'.format(self.request_body.name))

        return ', '.join(input_signature)

    @property
    def call_args(self):

        call_args_signature = []

        # -- path parameters
        path = re.sub(
            r'\{(?P<parameter>[\w\_]+)\}',
            lambda x: '${{{}}}'.format(
                to_camelcase(x.groupdict()['parameter'], first_lower=True)),
            self.path)

        if self.path_parameters:
            call_args_signature.append('`{}`'.format(path))

        else:
            call_args_signature.append("'{}'".format(path))

        #
        # BODY
        #
        # -- body
        if not self.request_body.is_empty():
            call_args_signature.append('body')

        # -- when body is missing
        elif self.method in ['put', 'post']:
            call_args_signature.append('{}')

        #
        # OPTIONS (INCLUDING QUERY PARAMS)
        #
        # -- query
        options = []
        if not self.request_query.is_empty():
            options.append('params')

        # -- authorization
        options.append(
            "authorizationRequired: {}".format(
                self.authorization_required and 'true' or 'false'))

        call_args_signature.append('{{ {} }}'.format(', '.join(options)))

        return ', '.join(call_args_signature)

    @property
    def call_args_without_path(self):

        call_args_signature = []

        # -- path parameters
        if self.path_parameters:
            call_args_signature.append(
                ', '.join([
                    to_camelcase(p['name'], first_lower=True)
                    for p in self.path_parameters]))

        # -- query
        if not self.request_query.is_empty():
            call_args_signature.append('params')

        # -- body
        if not self.request_body.is_empty():
            call_args_signature.append('body')

        return ', '.join(call_args_signature)

    def to_arg(self, parameter):
        if parameter['type'] == int:
            type_ = 'number'

        elif parameter['type'] == str:
            type_ = 'string'

        else:
            type_ = 'any'

        return '{arg}: {type}'.format(
            arg=to_camelcase(parameter['name'], first_lower=True),
            type=type_)

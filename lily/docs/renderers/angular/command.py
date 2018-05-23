# -*- coding: utf-8 -*-

from .interface import Interface
from .signature import Signature
from .utils import to_camelcase, normalize_indentation


class Command:

    def __init__(self, name, conf):
        self.name = name
        self.conf = conf

        # -- access attributes
        self.method = self.conf['method'].lower()
        self.camel_name = to_camelcase(self.name, first_lower=True)

        # -- META
        self.domain_id = self.conf['meta']['domain']['id']
        self.domain_name = self.conf['meta']['domain']['name']
        self.title = self.conf['meta']['title']
        self.description = self.conf['meta'].get('description')

        # -- ACCESS
        self.is_private = self.conf['access']['is_private']

        # -- REQUEST / RESPONSE
        self.path = self.conf['path_conf']['path']
        self.path_parameters = self.conf['path_conf']['parameters']
        self.request_query = Interface(
            self.name,
            Interface.TYPES.REQUEST_QUERY,
            self.conf['schemas']['input_query'])
        self.request_body = Interface(
            self.name,
            Interface.TYPES.REQUEST_BODY,
            self.conf['schemas']['input_body'])
        self.response = Interface(
            self.name,
            Interface.TYPES.RESPONSE,
            self.conf['schemas']['output'])
        self.signature = Signature(
            self.path,
            self.path_parameters,
            self.request_query,
            self.request_body)

    @property
    def header(self):
        if self.description:
            return normalize_indentation('''
            /**
             * {self.title}
             * -------------
             *
             * {self.description}
             */
            ''', 0).format(self=self)

        else:
            return normalize_indentation('''
            /**
             * {self.title}
             */
            ''', 0).format(self=self)

    def render(self):

        if self.method == 'get':
            return normalize_indentation('''
            {self.header}
            public {self.camel_name}({self.signature.input}): DataState<{self.response.name}> {{
                return this.client.getDataState<{self.response.name}>({self.signature.call_args});
            }}
            ''', 0).format(self=self)  # noqa

        else:
            return normalize_indentation('''
            {self.header}
            public {self.camel_name}({self.signature.input}): Observable<{self.response.name}> {{
                return this.client
                    .{self.method}<{self.response.name}>({self.signature.call_args})
                    .pipe(filter(x => !_.isEmpty(x)));
            }}
            ''', 0).format(self=self)  # noqa

    def render_facade(self):

        if self.method == 'get':
            return normalize_indentation('''
                {self.camel_name}({self.signature.input}): DataState<{self.response.name}> {{
                    return this.{self.domain_id}Domain.{self.camel_name}({self.signature.call_args});
                }}
            ''', 0).format(self=self)  # noqa

        else:
            return normalize_indentation('''
                {self.camel_name}({self.signature.input}): Observable<{self.response.name}> {{
                    return this.{self.domain_id}Domain.{self.camel_name}({self.signature.call_args});
                }}
            ''', 0).format(self=self)  # noqa

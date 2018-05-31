# -*- coding: utf-8 -*-

import json

from .interface import Interface
from .signature import Signature
from .utils import to_camelcase
from lily.base.utils import normalize_indentation


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
        self.authorization_required = (
            self.conf['access']['access_list'] is not None)

        # -- REQUEST / RESPONSE
        self.path = self.conf['path_conf']['path']
        self.path_parameters = self.conf['path_conf']['parameters']

        # -- request query
        request_query_schema = self.conf['schemas'].get(
            'input_query') or {'schema': None, 'uri': None}

        self.request_query = Interface(
            self.name,
            Interface.TYPES.REQUEST_QUERY,
            request_query_schema['schema'],
            request_query_schema['uri'])

        # -- request body
        request_body_schema = self.conf['schemas'].get(
            'input_body') or {'schema': None, 'uri': None}

        self.request_body = Interface(
            self.name,
            Interface.TYPES.REQUEST_BODY,
            request_body_schema['schema'],
            request_body_schema['uri'])

        # -- response
        response_schema = self.conf['schemas']['output']
        self.response = Interface(
            self.name,
            Interface.TYPES.RESPONSE,
            response_schema['schema'],
            response_schema['uri'],
            bulk_read_field=self.get_bulk_read_field())
        self.signature = Signature(
            self.method,
            self.path,
            self.path_parameters,
            self.authorization_required,
            self.request_query,
            self.request_body,
            bulk_read_field=self.get_bulk_read_field())

        # -- EXAMPLES
        self.examples = self.conf.get('examples', {})

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

    def get_bulk_read_field(self):

        if not self.name.startswith('BULK_READ'):
            return None

        try:
            schema = self.conf['schemas']['output']['schema']
            fields = list(schema['properties'].keys())

        except KeyError:
            return None

        if len(fields) == 1:
            field = fields[0]
            if field and schema['properties'][field]['type'] == 'array':
                return field

        return None

    def render(self):

        if self.get_bulk_read_field() and self.method != 'get':
            return normalize_indentation('''
            {self.header}
            public {self.camel_name}({self.signature.input}): Observable<X.{self.response.name}Entity[]> {{
                return this.client
                    .{self.method}<X.{self.response.name}>({self.signature.call_args})
                    .pipe(map(x => x.{bulk_read_field}));
            }}
            ''', 0).format(  # noqa
                self=self,
                # FIXME: !!! should be this as soon as integration is over
                # bulk_read_field=self.get_bulk_read_field(),
                bulk_read_field='data',
            )

        elif self.get_bulk_read_field() and self.method == 'get':
            return normalize_indentation('''
            {self.header}
            public {self.camel_name}({self.signature.input}): DataState<X.{self.response.name}Entity[]> {{
                return this.client.getDataState<X.{self.response.name}Entity[]>({self.signature.call_args});
            }}
            ''', 0).format(self=self)  # noqa

        elif self.method == 'get':
            return normalize_indentation('''
            {self.header}
            public {self.camel_name}({self.signature.input}): DataState<X.{self.response.name}> {{
                return this.client.getDataState<X.{self.response.name}>({self.signature.call_args});
            }}
            ''', 0).format(self=self)  # noqa

        else:
            return normalize_indentation('''
            {self.header}
            public {self.camel_name}({self.signature.input}): Observable<X.{self.response.name}> {{
                return this.client
                    .{self.method}<X.{self.response.name}>({self.signature.call_args})
                    .pipe(filter(x => !_.isEmpty(x)));
            }}
            ''', 0).format(self=self)  # noqa

    def render_facade(self):

        if self.get_bulk_read_field():
            return normalize_indentation('''
                {self.camel_name}({self.signature.input}): DataState<X.{self.response.name}Entity[]> {{
                    return this.{self.domain_id}Domain.{self.camel_name}({self.signature.call_args_without_path});
                }}
            ''', 0).format(self=self)  # noqa

        elif self.method == 'get':
            return normalize_indentation('''
                {self.camel_name}({self.signature.input}): DataState<X.{self.response.name}> {{
                    return this.{self.domain_id}Domain.{self.camel_name}({self.signature.call_args_without_path});
                }}
            ''', 0).format(self=self)  # noqa

        else:
            return normalize_indentation('''
                {self.camel_name}({self.signature.input}): Observable<X.{self.response.name}> {{
                    return this.{self.domain_id}Domain.{self.camel_name}({self.signature.call_args_without_path});
                }}
            ''', 0).format(self=self)  # noqa

    def render_examples(self):

        examples_blocks = []
        for example_name in sorted(self.examples.keys()):
            example_response = self.examples[example_name]['response']

            examples_blocks.append(normalize_indentation('''
                "{example_name}": {example_response}
            ''', 0).format(
                example_name=example_name,
                example_response=json.dumps(
                    example_response, sort_keys=True, indent=4)))

        return normalize_indentation('''
            /**
             * Examples for {self.name}
             */
            export const {command_name}Examples = {{
            {examples}
            }}
        ''', 0).format(
            self=self,
            command_name=to_camelcase(self.name),
            examples=normalize_indentation(',\n\n'.join(examples_blocks), 4))
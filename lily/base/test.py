# -*- coding: utf-8 -*-

import json
from copy import deepcopy

from django.core.urlresolvers import get_resolver
from django.test import Client as DjangoClient
from django.conf import settings


class MissingConfError(Exception):
    pass


# FIXME: test it!
class Client(DjangoClient):

    resolver = get_resolver(None)

    def post(self, *args, **kwargs):
        return self._make_request('post', *args, **kwargs)

    def get(self, *args, **kwargs):
        return self._make_request('get', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._make_request('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._make_request('delete', *args, **kwargs)

    def _make_request(self, http_verb, *args, **kwargs):
        response = getattr(super(Client, self), http_verb)(*args, **kwargs)

        fn = self.resolver.resolve(response.request["PATH_INFO"]).func

        try:
            command_conf = getattr(fn.view_class, http_verb).command_conf

            try:
                with open(settings.LILY_DOCS_TEST_EXAMPLES_FILE, 'r+') as f:
                    examples = json.loads(f.read() or '{}')

            except FileNotFoundError:
                examples = {}

            command_name = command_conf['name']
            examples.setdefault(command_name, {})

            response_json = response.json()
            example_key = '{status} ({event})'.format(
                status=response.status_code,
                event=response_json['@event'])

            # -- construct the request
            request = {}
            path = response.request["PATH_INFO"]

            if response.request.get("QUERY_STRING"):
                path = '{path}?{query_string}'.format(
                    path=path,
                    query_string=response.request["QUERY_STRING"])

            request['path'] = path
            request_kwargs = deepcopy(kwargs)
            data = request_kwargs.get('data')
            if data:
                data = request_kwargs.pop('data')

                if http_verb.upper() in ['POST', 'PUT']:
                    if isinstance(data, dict):
                        request['content'] = data

                    else:
                        request['content'] = json.loads(data)

            if request_kwargs:
                def normalize_header(h):
                    return h.upper().replace('_', '-').replace('HTTP-', '')

                request['headers'] = {
                    normalize_header(h): v
                    for h, v in request_kwargs.items()}

            examples[command_name][example_key] = {
                'method': http_verb,
                'description': response_json['@event'],
                'request': request,
                'response': {
                    'status': response.status_code,
                    'content_type': response['Content-Type'],
                    'content': response_json,
                },
            }
            # try:
            #     payload = str(
            #         response.request['wsgi.input'].read(), 'utf8')

            #     if payload:
            #         examples[command_name][example_key]['request'] = {
            #             'content_type': response.request['CONTENT_TYPE'],
            #             'content': json.loads(payload),
            #         }

            # except KeyError:
            #     pass

            with open(settings.LILY_DOCS_TEST_EXAMPLES_FILE, 'w') as f:
                f.write(json.dumps(examples, indent=4))

        except AttributeError:
            raise MissingConfError({
                'method': http_verb,
                'path': response.request['PATH_INFO'],
            })

        return response

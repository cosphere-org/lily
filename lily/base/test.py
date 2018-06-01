# -*- coding: utf-8 -*-

import os
import json
from copy import deepcopy
from unittest.mock import patch
from contextlib import ContextDecorator

from django.urls import get_resolver
from django.test import Client as DjangoClient

from lily.conf import settings


class MissingConfError(Exception):
    pass


def get_examples_filepath():
    return os.path.join(settings.LILY_CACHE_DIR, 'api_examples.json')


class override_settings(ContextDecorator):  # noqa

    def __init__(self, **settings):
        self.settings = settings
        self.patchers = []

    def __enter__(self):

        self.patchers = [
            patch.object(settings, key, value)
            for key, value in self.settings.items()
        ]
        for p in self.patchers:
            p.start()

        return self

    def __exit__(self, exc_type, exc, exc_tb):
        for p in self.patchers:
            p.stop()


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

        def assure_path_exists(path):
            dir_path = os.path.dirname(path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        assure_path_exists(get_examples_filepath())

        response = getattr(super(Client, self), http_verb)(*args, **kwargs)

        fn = self.resolver.resolve(response.request['PATH_INFO']).func

        try:
            command_conf = getattr(fn.view_class, http_verb).command_conf

            try:
                with open(get_examples_filepath(), 'r+') as f:
                    examples = json.loads(f.read() or '{}')

            except FileNotFoundError:
                examples = {}

            command_name = command_conf['name']
            examples.setdefault(command_name, {})

            response_json = response.json()

            # -- render example key name
            try:
                extra_desc = kwargs.pop('extra_desc')

            except KeyError:
                example_key = '{status} ({event})'.format(
                    status=response.status_code,
                    event=response_json['@event'])

            else:
                example_key = '{status} ({event}) - {extra_desc}'.format(
                    status=response.status_code,
                    event=response_json['@event'],
                    extra_desc=extra_desc)

            # -- construct the request
            request = {}
            path = response.request['PATH_INFO']

            if response.request.get('QUERY_STRING'):
                path = '{path}?{query_string}'.format(
                    path=path,
                    query_string=response.request['QUERY_STRING'])

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

            with open(get_examples_filepath(), 'w') as f:
                f.write(json.dumps(examples, indent=4))

        except AttributeError:
            raise MissingConfError({
                'method': http_verb,
                'path': response.request['PATH_INFO'],
            })

        return response


import os
import json
from copy import deepcopy
from unittest.mock import patch
from contextlib import ContextDecorator
import requests

from django.urls import get_resolver
from django.test import Client as DjangoClient, SimpleTestCase
from django.test.utils import CaptureQueriesContext

from django.db import DEFAULT_DB_ALIAS, connections
from lily_assistant.config import Config

from lily.conf import settings


class MissingConfError(Exception):
    pass


def get_examples_filepath():
    return os.path.join(Config.get_lily_path(), 'examples.json')


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


class AssertNumQueriesContext(CaptureQueriesContext):

    def __init__(self, test_case, num, connection):
        self.test_case = test_case
        self.num = num
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        executed = len(self)
        self.test_case.assertEqual(
            executed, self.num,
            "%d queries executed, %d expected\nCaptured queries were:\n%s" % (
                executed, self.num,
                '\n'.join(
                    '%d. %s' % (i, query['sql'])
                    for i, query in enumerate(self.captured_queries, start=1)
                )
            )
        )


class TestCase(SimpleTestCase):

    @property
    def is_unit_type(self):
        return settings.LILY_TEST_CLIENT_TYPE.upper() == 'UNIT'

    @property
    def authorization_header(self):
        if self.is_unit_type:
            return 'HTTP_AUTHORIZATION'

        return 'Authorization'

    def _fixture_setup(self, *args, **kwargs):
        if self.is_unit_type:
            super(TestCase, self)._fixture_setup(*args, **kwargs)

    def _fixture_teardown(self, *args, **kwargs):
        if self.is_unit_type:
            super(TestCase, self)._fixture_teardown(*args, **kwargs)

    def assertNumQueries(self, num, using=DEFAULT_DB_ALIAS):  # noqa

        return AssertNumQueriesContext(self, num, connections[using])


class E2EClient:

    def post(self, path, data=None, json=None, files=None, **headers):
        return self._make_request(
            'post',
            path,
            data=data,
            json=json,
            files=files,
            headers=headers)

    def get(self, path, data=None, json=None, **headers):
        return self._make_request(
            'get',
            path,
            data=data,
            json=json,
            headers=headers)

    def put(self, path, data=None, json=None, **headers):
        return self._make_request(
            'put',
            path,
            data=data,
            json=json,
            headers=headers)

    def delete(self, path, data=None, json=None, **headers):
        return self._make_request(
            'delete',
            path,
            data=data,
            json=json,
            headers=headers)

    def _make_request(
        self,
        http_verb,
        path,
        data=None,
        json=None,
        files=None,
        headers=None
    ):

        payload = {}
        if json:
            payload = {'json': json}

        if data and http_verb in ['put', 'post']:
            payload = {'data': data}

        if data and http_verb in ['get', 'delete']:
            payload = {'params': data}

        response = getattr(requests, http_verb)(
            self._get_url(path),
            headers=headers or {},
            files=files or {},
            verify=self._verify_ssl,
            **payload)

        return response

    def _get_url(self, path):
        path = path.strip()
        if not path.startswith('/'):
            path = f'/{path}'

        return f'{settings.LILY_TEST_CLIENT_BASE_URI}{path}'

    @property
    def _verify_ssl(self):
        return settings.LILY_TEST_CLIENT_VERIFY_SSL


class UnitClient(DjangoClient):

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

        # -- handling json case
        if 'json' in kwargs:
            kwargs['data'] = json.dumps(kwargs['json'])
            kwargs['content_type'] = 'application/json'
            del kwargs['json']

        response = getattr(super(UnitClient, self), http_verb)(*args, **kwargs)

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

            try:
                response_content = response.json()

            except ValueError:
                response_content = str(response.content, encoding='utf-8')
                event = None

            else:
                event = response_content['@event']

            # -- render example key name
            try:
                extra_desc = kwargs.pop('extra_desc')

            except KeyError:
                if event:
                    example_key = f'{response.status_code} ({event})'  # noqa

                else:
                    example_key = f'{response.status_code}'

            else:
                if event:
                    example_key = (
                        f'{response.status_code} ({event}) - {extra_desc}')

                else:
                    example_key = f'{response.status_code} - {extra_desc}'

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
                'description': event,
                'request': request,
                'response': {
                    'status': response.status_code,
                    'content_type': response['Content-Type'],
                    'content': response_content,
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


def Client():  # noqa

    if settings.LILY_TEST_CLIENT_TYPE.upper() == 'UNIT':
        return UnitClient()

    else:
        return E2EClient()

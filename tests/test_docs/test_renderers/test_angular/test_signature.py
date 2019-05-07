
from django.test import TestCase

from lily.docs.renderers.angular.signature import Signature


class MockInterface:

    def __init__(self, name=None, is_empty=False):
        self.name = name
        self._is_empty = is_empty

    def is_empty(self):
        return self._is_empty


class SignatureTestCase(TestCase):

    #
    # INPUT
    #
    def test_input__nothing(self):

        s = Signature(
            method='get',
            path='/cards',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.input == ''

    def test_input__path_parameters(self):

        # -- single parameter
        s = Signature(
            method='get',
            path='/cards/{card_id}',
            path_parameters=[{'name': 'card_id', 'type': int}],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.input == 'cardId: number'

        # -- multiple parameters
        s = Signature(
            method='get',
            path='/cards/{card_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
                {'name': 'name', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.input == 'cardId: number, userId: string, name: string'

    def test_input__query_params(self):

        s = Signature(
            method='get',
            path='/cards/',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(name='ReadCardRequestQuery'),
            request_body=MockInterface(is_empty=True))

        assert s.input == 'params: X.ReadCardRequestQuery'

    def test_input__path_parameters_and_query_params(self):

        s = Signature(
            method='get',
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(name='ReadCardRequestQuery'),
            request_body=MockInterface(is_empty=True))

        assert s.input == (
            'cardId: number, userId: string, params: X.ReadCardRequestQuery')

    def test_input__body_params(self):

        s = Signature(
            method='put',
            path='/paths/',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(name='ReadCardRequestBody'))

        assert s.input == 'body: X.ReadCardRequestBody'

    def test_input__path_parameters_and_body_params(self):

        s = Signature(
            method='put',
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(name='ReadCardRequestBody'))

        assert s.input == (
            'cardId: number, userId: string, body: X.ReadCardRequestBody')

    #
    # CALL_ARGS
    #
    def test_call_args__nothing(self):

        s = Signature(
            method='get',
            path='/cards',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args == "'/cards', { authorizationRequired: true }"

    def test_call_args__path_parameters(self):

        # -- single parameter
        s = Signature(
            method='get',
            path='/cards/{card_id}',
            path_parameters=[{'name': 'card_id', 'type': int}],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args == (
            '`/cards/${cardId}`, { authorizationRequired: true }')

        # -- multiple parameters
        s = Signature(
            method='get',
            path='/cards/{card_id}/{name}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
                {'name': 'name', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args == (
            '`/cards/${cardId}/${name}/users/${userId}`, '
            '{ authorizationRequired: true }')

    def test_call_args__query_params(self):

        s = Signature(
            method='get',
            path='/paths/',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(name='ReadPathRequestQuery'),
            request_body=MockInterface(is_empty=True))

        assert s.call_args == (
            "'/paths/', { params, authorizationRequired: true }")

    def test_call_args__path_parameters_and_query_params(self):

        s = Signature(
            method='get',
            path='/paths/{path_id}/users/{user_id}',
            path_parameters=[
                {'name': 'path_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(name='ReadPathRequestQuery'),
            request_body=MockInterface(is_empty=True))

        assert s.call_args == (
            '`/paths/${pathId}/users/${userId}`, '
            '{ params, authorizationRequired: true }')

    def test_call_args__body_params(self):

        s = Signature(
            method='post',
            path='/cards/',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(name='ReadCardRequestBody'))

        assert s.call_args == (
            "'/cards/', body, { authorizationRequired: true }")

    def test_call_args__path_parameters_and_body_params(self):

        s = Signature(
            method='post',
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(name='ReadCardRequestBody'))

        assert s.call_args == (
            '`/cards/${cardId}/users/${userId}`, '
            'body, { authorizationRequired: true }')

    def test_call_args__path_parameters_and_no_body(self):

        s = Signature(
            method='post',
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=False,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args == (
            '`/cards/${cardId}/users/${userId}`, '
            '{}, { authorizationRequired: false }')

    def test_call_args__bulk_read_field_and_path_parameters(self):

        s = Signature(
            method='get',
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True),
            bulk_read_field='cards')

        assert (
            s.call_args ==
            '`/cards/${cardId}/users/${userId}`, '
            '{ authorizationRequired: true }')

    def test_call_args__bulk_read_field_and_path_parameters_and_query_params(self):  # noqa

        s = Signature(
            method='get',
            path='/cards/{card_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=False),
            request_body=MockInterface(is_empty=True),
            bulk_read_field='cards')

        assert (
            s.call_args ==
            '`/cards/${cardId}`, { params, authorizationRequired: true }')

    #
    # CALL_ARGS_WITHOUT_PATH
    #
    def test_call_args_without_path__nothing(self):

        s = Signature(
            method='get',
            path='/cards',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args_without_path == ''

    def test_call_args_without_path__path_parameters(self):

        # -- single parameter
        s = Signature(
            method='get',
            path='/cards/{card_id}',
            path_parameters=[{'name': 'card_id', 'type': int}],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args_without_path == 'cardId'

        # -- multiple parameters
        s = Signature(
            method='get',
            path='/cards/{card_id}/{name}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
                {'name': 'name', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(is_empty=True))

        assert s.call_args_without_path == 'cardId, userId, name'

    def test_call_args_without_path__query_params(self):

        s = Signature(
            method='get',
            path='/paths/',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(name='ReadPathRequestQuery'),
            request_body=MockInterface(is_empty=True))

        assert s.call_args_without_path == 'params'

    def test_call_args_without_path__path_parameters_and_query_params(self):

        s = Signature(
            method='get',
            path='/paths/{path_id}/users/{user_id}',
            path_parameters=[
                {'name': 'path_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(name='ReadPathRequestQuery'),
            request_body=MockInterface(is_empty=True))

        assert s.call_args_without_path == 'pathId, userId, params'

    def test_call_args_without_path__body_params(self):

        s = Signature(
            method='post',
            path='/cards/',
            path_parameters=[],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(name='ReadCardRequestBody'))

        assert s.call_args_without_path == 'body'

    def test_call_args_without_path__path_parameters_and_body_params(self):

        s = Signature(
            method='post',
            path='/cards/{card_id}/users/{user_id}',
            path_parameters=[
                {'name': 'card_id', 'type': int},
                {'name': 'user_id', 'type': str},
            ],
            authorization_required=True,
            request_query=MockInterface(is_empty=True),
            request_body=MockInterface(name='ReadCardRequestBody'))

        assert s.call_args_without_path == 'cardId, userId, body'

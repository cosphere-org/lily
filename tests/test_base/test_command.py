# -*- coding: utf-8 -*-

import json

from django.test import TestCase
from django.db.utils import DatabaseError
from django.contrib.auth.models import User
from django.views.generic import View
from django_fake_model import models as fake_models
from django.db import models
from mock import Mock
import pytest

from lily.base.command import (
    EventFactory,
    Meta,
    Input,
    Output,
    command
)
from lily.base import serializers
from lily.base import parsers

from .test_parsers import RequestGet


logger = Mock()


event = EventFactory(logger)


def to_json(response, content_field='content'):
    return json.loads(str(getattr(response, content_field), encoding='utf8'))


class Request:
    pass


def dump_to_bytes(data):
    return bytes(json.dumps(data), 'utf8')


def get_auth_headers(user_id, account_type='SUPER_PREMIUM'):
    return {
        'HTTP_X_CS_ACCOUNT_TYPE': account_type,
        'HTTP_X_CS_USER_ID': user_id,
        'SERVER_NAME': 'yo',
    }


class MetaTestCase(TestCase):

    def test_required_fields(self):
        # -- missing title
        with pytest.raises(TypeError):
            Meta('this is it!', ['api', 'this'])

        # -- missing description
        with pytest.raises(TypeError):
            Meta('hi there', ['api', 'this'])

        # -- missing tags
        with pytest.raises(TypeError):
            Meta('hi there', 'this is it!')

    def test_arguments_are_saved(self):
        m = Meta('hi there', 'this is it', ['a', 'b'])
        assert m.title == 'hi there'
        assert m.description == 'this is it'
        assert m.tags == ['a', 'b']

    def test_serialize(self):
        m = Meta('hi there', 'this is it', ['a', 'b'])

        assert m.serialize() == {
            'title': 'hi there',
            'description': 'this is it',
            'tags': ['a', 'b'],
        }


class InputTestCase(TestCase):

    def setUp(self):
        User.objects.all().delete()

    @pytest.fixture(autouse=True)
    def initfitures(self, mocker):
        self.mocker = mocker

    #
    # parse
    #
    def test_parse__makes_the_right_calls(self):
        parse_body = self.mocker.patch.object(Input, 'parse_body')
        parse_body.return_value = [{}, {}]
        parse_query = self.mocker.patch.object(Input, 'parse_query')
        get_user = self.mocker.patch.object(Input, 'get_user')
        query_parser, body_parser = Mock(), Mock()
        request = Mock()

        # -- both query and body parsers
        i = Input(
            query_parser=query_parser, body_parser=body_parser, with_user=True)
        i.parse(request, command_name='MAKE_IT')

        assert parse_body.call_count == 1
        assert parse_query.call_count == 1
        assert get_user.call_count == 1

    #
    # parse_query
    #
    def test_parse_query__all_ok(self):
        class QueryParser(parsers.QueryParser):
            title = parsers.CharField()
            prices = parsers.ListField(child=parsers.IntegerField())

        input = Input(query_parser=QueryParser)
        input.event = event

        request = Mock(
            GET=RequestGet(title=['hi there'], prices=[67, 89, 11]),
            user_id=902)

        data = input.parse_query(request)

        assert data == {'title': 'hi there', 'prices': [67, 89, 11]}

    def test_parse_query__event__query_did_not_validate(self):
        class QueryParser(parsers.QueryParser):
            title = parsers.CharField()
            prices = parsers.ListField(child=parsers.IntegerField())

        input = Input(query_parser=QueryParser)
        input.event = event

        request = Mock(
            GET=RequestGet(title=['hi there'], prices=['what']),
            user_id=902)

        try:
            input.parse_query(request)

        except event.BrokenRequest as e:
            assert e.data == {
                '@type': 'error',
                '@event': 'QUERY_DID_NOT_VALIDATE',
                'user_id': 902,
                'errors': {
                    'prices': ['A valid integer is required.'],
                },
            }

        else:
            raise AssertionError

    #
    # parse_query
    #
    def _prepare_body_parser(self):
        class BodyParser(parsers.BodyParser):
            title = parsers.CharField()
            amount = parsers.IntegerField(max_value=19)

        input = Input(body_parser=BodyParser)
        input.event = event

        return input

    def test_parse_body__all_ok(self):
        input = self._prepare_body_parser()

        request = Mock(
            body=b'{"title": "hi there", "amount": "18"}', user_id=902)

        data, raw_data = input.parse_body(request, command_name='MAKE_IT')

        assert data == {'amount': 18, 'title': 'hi there'}
        assert raw_data == {'amount': '18', 'title': 'hi there'}

    def test_parse_body__broken_json(self):
        input = self._prepare_body_parser()

        request = Mock(body='{not json', user_id=902)
        try:
            input.parse_body(request, command_name='MAKE_IT')

        except input.event.BrokenRequest as error:
            assert error.event == 'BODY_JSON_DID_NOT_PARSE'
            assert error.data == {
                '@type': 'error',
                '@event': 'BODY_JSON_DID_NOT_PARSE',
                'user_id': 902,
            }
            assert error.is_critical

        else:
            raise AssertionError('didn\'t raise error!')

    def test_parse_body__invalid_payload(self):
        input = self._prepare_body_parser()

        # -- amount too big error
        request = Mock(
            body=b'{"title": "hi there", "amount": 20}', user_id=902)
        try:
            input.parse_body(request, command_name='MAKE_IT')

        except input.event.BrokenRequest as error:
            assert error.event == 'BODY_DID_NOT_VALIDATE'
            assert error.data == {
                '@type': 'error',
                '@event': 'BODY_DID_NOT_VALIDATE',
                'user_id': 902,
                'errors': {
                    'amount': [
                        'Ensure this value is less than or equal to 19.'
                    ]
                }
            }
            assert not error.is_critical

        else:
            raise AssertionError('didn\'t raise error!')

        # -- amount is title
        request = Mock(body=b'{"amount": 19}', user_id=902)
        try:
            input.parse_body(request, command_name='MAKE_IT')

        except input.event.BrokenRequest as error:
            assert error.event == 'BODY_DID_NOT_VALIDATE'
            assert error.data == {
                '@type': 'error',
                '@event': 'BODY_DID_NOT_VALIDATE',
                'user_id': 902,
                'errors': {
                    'title': ['This field is required.']
                }
            }
            assert not error.is_critical

        else:
            raise AssertionError('didn\'t raise error!')

    #
    # get_user
    #
    def test_get_user__all_ok(self):
        input = self._prepare_body_parser()

        u = User.objects.create_user(id=19, username='hi there')
        request = Mock(body=b'{"title": "hi", "amount": 19}', user_id=u.id)

        fetched_user = input.get_user(request)

        assert fetched_user == u

    def test_get_user__does_not_exist(self):
        input = self._prepare_body_parser()

        request = Mock(body=b'{"title": "hi", "amount": 19}', user_id=190)
        try:
            input.get_user(request)

        except input.event.AuthError as error:
            assert error.event == 'COULD_NOT_FIND_USER'
            assert error.data == {
                '@type': 'error',
                '@event': 'COULD_NOT_FIND_USER',
                'user_id': 190,
            }
            assert error.is_critical

        else:
            raise AssertionError('didn\'t raise error!')


class OutputTestCase(TestCase):

    def test_required_fields(self):
        # -- missing logger
        with pytest.raises(TypeError):
            Output()

    def test_arguments_are_saved(self):
        serializer = Mock()

        o = Output(logger=logger, serializer=serializer)

        assert o.serializer == serializer
        assert o.logger == logger


class FakeClient(fake_models.FakeModel):
    name = models.CharField(max_length=100)


@FakeClient.fake_me
class TestView(View):

    class BodyParser(parsers.BodyParser):

        name = parsers.CharField()
        age = parsers.IntegerField()

    class ClientSerializer(serializers.ModelSerializer):
        _type = 'client'

        _command_links = [
            serializers.CommandLink(
                name='MAKE_IT_BETTER',
                parameters={'card_id': '$response.body#/card_id'},
                description='...'),
        ]

        card_id = serializers.SerializerMethodField()

        class Meta:
            model = FakeClient
            fields = ('name', 'card_id')

        def get_card_id(self, instance):
            return 190

    class SimpleSerializer(serializers.Serializer):
        _type = 'simple'

        amount = serializers.IntegerField()

    meta = Meta(
        title='hi there',
        description='it is made for all',
        tags=['test view'])

    input = Input(
        with_user=True,
        body_parser=BodyParser)

    output = Output(serializer=ClientSerializer, logger=logger)

    @command(
        name='MAKE_IT',
        meta=meta,
        input=input,
        output=output,
        access_list=['PREMIUM', 'SUPER_PREMIUM'])
    def post(self, request, user_id):
        raise event.Success(
            'MADE_IT',
            context=request,
            instance=FakeClient(name="Jake"))

    @command(
        name='GET_IT',
        meta=Meta(
            title='get', description='get it...', tags=['get']),
        input=Input(with_user=False),
        output=output,
        access_list=None)
    def get(self, request):
        raise event.Success(
            'GET_IT',
            context=request,
            instance=FakeClient(name="Jake"))

    @command(
        name='BREAK',
        meta=Meta(
            title='break', description='break it...', tags=['break']),
        input=Input(with_user=False),
        output=Output(logger=logger, serializer=SimpleSerializer),
        access_list=None)
    def put(self, request):

        raise event.Success(
            'BROKEN',
            context=request,
            data=json.loads(request.body.decode('utf8')))

    @command(
        name='ATOMIC',
        meta=Meta(
            title='atomic', description='atomic it...', tags=['atomic']),
        input=Input(with_user=False),
        is_atomic=True,
        output=Output(logger=logger, serializer=SimpleSerializer),
        access_list=None)
    def delete(self, request):

        self.some_stuff()
        raise event.Success('ATOMIC', context=request, data={})

    def some_stuff(self):
        pass


class CommandTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        User.objects.all().delete()

    def test_success(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            body=dump_to_bytes({"name": "John", "age": 81}),
            META=get_auth_headers(u.id, 'SUPER_PREMIUM'))
        self.mocker.patch.object(
            serializers,
            'COMMANDS_CONF',
            {
                'MAKE_IT_BETTER': {
                    'service_base_uri': 'http://192.11.2.1:9000',
                    'method': 'post',
                    'path_conf': {
                        'path': '/payment_cards/{card_id}/sth/',
                        'parameters': [
                            {
                                'name': 'card_id',
                                'in': 'path',
                                'description': None,
                                'required': True,
                                'type': 'integer'
                            },
                        ],
                    },
                    'access_list': ['SUPER_PREMIUM'],
                },
            })

        view = TestView()

        response = view.post(request, 11)

        assert response.status_code == 200
        assert to_json(response) == {
            '@type': 'client',
            '@event': 'MADE_IT',
            '@commands': {
                'MAKE_IT_BETTER': {
                    'name': 'MAKE_IT_BETTER',
                    'method': 'post',
                    'uri': 'http://192.11.2.1:9000/payment_cards/190/sth/',
                },
            },
            'name': 'Jake',
            'card_id': 190,
        }

    #
    # AUTHORIZATION
    #
    def test_access_denied__missing_headers(self):

        request = Request()
        request.body = dump_to_bytes({"name": "John", "age": 81})
        request.META = {}
        view = TestView()

        response = view.post(request, 12)

        assert response.status_code == 403
        assert to_json(response) == {
            '@type': 'error',
            '@event': 'ACCESS_DENIED',
            'user_id': 'anonymous',
        }

    def test_no_authorization(self):

        request = Request()
        request.body = dump_to_bytes({"name": "John", "age": 81})
        request.META = {}
        view = TestView()

        response = view.get(request)

        assert response.status_code == 200

    #
    # CONF
    #
    def test_conf__command_name_attached_to_the_request(self):

        u = User.objects.create_user(username='jacky')
        request = Request()
        request.body = dump_to_bytes({"name": "John", "age": 81})
        request.META = get_auth_headers(u.id, 'SUPER_PREMIUM')
        view = TestView()

        view.post(request, 15)

        assert request.command_name == 'MAKE_IT'

    def test_conf__is_saved_on_function(self):

        assert TestView.post.command_conf == {
            'name': 'MAKE_IT',
            'method': 'post',
            'meta': TestView.meta,
            'path_params_annotations': {},
            'access_list': ['PREMIUM', 'SUPER_PREMIUM'],
            'input': TestView.input,
            'output': TestView.output,
        }

    #
    # INPUT
    #
    def test_input__body_parsing(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            body=dump_to_bytes({"name": "John", "age": 81}),
            META=get_auth_headers(u.id))
        view = TestView()

        response = view.post(request, 19)

        assert request.input.body == {"name": "John", "age": 81}
        assert response.status_code == 200

    def test_input__user(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            body=dump_to_bytes({"name": "John", "age": 81}),
            META=get_auth_headers(u.id))
        view = TestView()

        view.post(request, 19)

        assert request.input.user == u

    #
    # Response Validation
    #
    def test_response_valid(self):

        u = User.objects.create_user(username='jacky')
        meta = get_auth_headers(u.id)
        meta['SERVER_NAME'] = 'testserver'
        request = Mock(
            body=dump_to_bytes({"amount": 81}),
            user_id=u.id,
            META=meta)
        view = TestView()

        response = view.put(request)

        assert response.status_code == 200
        assert to_json(response) == {
            '@type': 'simple',
            '@event': 'BROKEN',
            'amount': 81,
        }

    def test_broken_response_validation(self):

        u = User.objects.create_user(username='jacky')
        meta = get_auth_headers(u.id)
        meta['SERVER_NAME'] = 'testserver'
        request = Mock(
            body=dump_to_bytes({"not_amount": 81}),
            user_id=u.id,
            META=meta)
        view = TestView()

        response = view.put(request)

        assert response.status_code == 400
        assert to_json(response) == {
            'user_id': u.id,
            '@type': 'error',
            '@event': 'RESPONSE_DID_NOT_VALIDATE',
            'errors': {'amount': ['This field is required.']},
        }

    #
    # ATOMICITY
    #
    def test_atomicity(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(user_id=u.id, META=get_auth_headers(u.id))
        view = TestView()
        self.mocker.patch.object(view, 'some_stuff').side_effect = [
            DatabaseError, Exception('hi there')]

        assert TestView.delete.__name__ == 'decorated_inner'

        # -- db error
        response = view.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'DATABASE_ERROR_OCCURRED',
            '@type': 'error',
            'user_id': u.id,
        }

        # -- generic error
        response = view.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'GENERIC_ERROR_OCCURRED',
            '@type': 'error',
            'errors': ['hi there'],
            'user_id': u.id,
        }

    #
    # GENERIC DOES NOT EXIST ERROR
    #
    def test_does_not_exist(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(user_id=u.id, META=get_auth_headers(u.id))
        view = TestView()
        self.mocker.patch.object(view, 'some_stuff').side_effect = (
            lambda: User.objects.get(id=4930))

        response = view.delete(request)

        assert response.status_code == 404
        assert to_json(response) == {
            '@event': 'COULD_NOT_FIND_USER',
            '@type': 'error',
            'user_id': u.id,
        }

    def test_multiple_objects_returned(self):

        u = User.objects.create_user(username='jacky')
        u = User.objects.create_user(username='jacks')
        request = Mock(user_id=u.id, META=get_auth_headers(u.id))
        view = TestView()
        self.mocker.patch.object(view, 'some_stuff').side_effect = (
            lambda: User.objects.get(username__contains='jack'))

        response = view.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'FOUND_MULTIPLE_INSTANCES_OF_USER',
            '@type': 'error',
            'user_id': u.id,
        }

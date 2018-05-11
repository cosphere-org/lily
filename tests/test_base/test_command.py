# -*- coding: utf-8 -*-

import logging
import json
from contextlib import ContextDecorator

from django.test import TestCase
from django.db.utils import DatabaseError
from django.contrib.auth.models import User
from django.views.generic import View
from django_fake_model import models as fake_models
from django.db import models, transaction
from mock import Mock
import pytest

from lily.base.command import command
from lily.base.access import Access
from lily.base.meta import Meta, Domain
from lily.base.input import Input
from lily.base.output import Output
from lily.base import serializers, parsers
from lily.base.events import EventFactory


logger = logging.getLogger()


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
        domain=Domain(id='test', name='test management'))

    input = Input(
        with_user=True,
        body_parser=BodyParser)

    output = Output(serializer=ClientSerializer)

    @command(
        name='MAKE_IT',
        meta=meta,
        input=input,
        output=output,
        access=Access(
            access_list=['PREMIUM', 'SUPER_PREMIUM'])
    )
    def post(self, request, user_id):
        raise self.event.Executed(
            event='MADE_IT',
            instance=FakeClient(name="Jake"))

    @command(
        name='GET_IT',
        meta=Meta(
            title='get',
            description='get it...',
            domain=Domain(id='get', name='get')),
        input=Input(with_user=False),
        output=output)
    def get(self, request):
        raise self.event.Executed(
            event='GET_IT',
            instance=FakeClient(name="Jake"))

    @command(
        name='BREAK',
        meta=Meta(
            title='break',
            description='break it...',
            domain=Domain(id='break', name='break')),
        output=Output(serializer=SimpleSerializer))
    def put(self, request):

        raise self.event.Executed(
            event='BROKEN',
            context=request,
            data=json.loads(request.body.decode('utf8')))

    @command(
        name='ATOMIC',
        meta=Meta(
            title='atomic',
            description='atomic it...',
            domain=Domain(id='atomic', name='atomic')),
        input=Input(with_user=False),
        is_atomic=True)
    def delete(self, request):

        self.some_stuff()

        raise self.event.Executed(event='ATOMIC', context=request, data={})

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
                    'access': {
                        'is_private': False,
                        'access_list': ['SUPER_PREMIUM'],
                    },
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
            'source': {
                'filepath': '/tests/test_base/test_command.py',
                'start_line': 99,
                'end_line': 111,
            },
            'meta': TestView.meta,
            'path_params_annotations': {},
            'access': Access(
                access_list=['PREMIUM', 'SUPER_PREMIUM']),
            'input': TestView.input,
            'output': TestView.output,
        }

    #
    # INPUT
    #
    def test_input__body_parsing(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            body=dump_to_bytes({'name': 'John', 'age': 81}),
            META=get_auth_headers(u.id))
        view = TestView()

        response = view.post(request, 19)

        assert request.input.body == {'name': 'John', 'age': 81}
        assert response.status_code == 200

    def test_input__user(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            body=dump_to_bytes({'name': 'John', 'age': 81}),
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
            body=dump_to_bytes({'amount': 81}),
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
            body=dump_to_bytes({'not_amount': 81}),
            user_id=u.id,
            email=None,
            origin=None,
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
    def test_atomicity__correct_exceptions_are_visible_for_the_roolback(self):

        class AtomicContext(ContextDecorator):

            exception = None

            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                pass

            def __exit__(self, exc_type, exc, exc_tb):
                self.__class__.exception = exc

        self.mocker.patch.object(transaction, 'atomic', AtomicContext)

        u = User.objects.create_user(username='jacky')
        request = Mock(
            user_id=u.id,
            email=None,
            origin=None,
            META=get_auth_headers(u.id))
        view = TestView()
        self.mocker.patch.object(view, 'some_stuff').side_effect = [
            # -- database error
            DatabaseError,

            # -- generic exception
            Exception('hi there'),

            # -- lily exception
            event.BrokenRequest(
                'ERROR!',
                context=event.Context(user_id=u.id, origin='SERVICE')
            ),
        ]

        # -- db error
        response = view.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'DATABASE_ERROR_OCCURRED',
            '@type': 'error',
            'user_id': u.id,
        }
        assert isinstance(AtomicContext.exception, DatabaseError)

        # -- generic error
        response = view.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'GENERIC_ERROR_OCCURRED',
            '@type': 'error',
            'errors': ['hi there'],
            'user_id': u.id,
        }
        assert isinstance(AtomicContext.exception, Exception)

        # -- not a success exception
        response = view.delete(request)

        assert response.status_code == 400
        assert to_json(response) == {
            '@event': 'ERROR!',
            '@type': 'error',
            '@origin': 'SERVICE',
            'user_id': u.id,
        }
        assert isinstance(AtomicContext.exception, event.BrokenRequest)

    def test_atomicity__success_response_is_not_visible_to_rollback(self):

        class AtomicContext(ContextDecorator):

            exception = None

            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                pass

            def __exit__(self, exc_type, exc, exc_tb):
                self.__class__.exception = exc

        self.mocker.patch.object(transaction, 'atomic', AtomicContext)

        u = User.objects.create_user(username='jacky')
        request = Mock(
            user_id=u.id,
            email=None,
            origin=None,
            META=get_auth_headers(u.id))
        view = TestView()
        self.mocker.patch.object(view, 'some_stuff').side_effect = [

            # -- lily success exception
            event.Executed(
                event='SUCCESS!',
                context=event.Context(user_id=u.id)
            ),

            # -- lily created exception
            event.Created(
                event='CREATED!',
                context=event.Context(user_id=u.id)
            ),

        ]

        # -- success exception
        response = view.delete(request)

        assert response.status_code == 200
        assert to_json(response) == {'@event': 'SUCCESS!'}
        assert AtomicContext.exception is None

        # -- created exception
        response = view.delete(request)

        assert response.status_code == 201
        assert to_json(response) == {'@event': 'CREATED!'}
        assert AtomicContext.exception is None

    #
    # GENERIC DOES NOT EXIST ERROR
    #
    def test_does_not_exist(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            user_id=u.id,
            email=None,
            origin=None,
            META=get_auth_headers(u.id))
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
        request = Mock(
            user_id=u.id,
            email=None,
            origin=None,
            META=get_auth_headers(u.id))
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

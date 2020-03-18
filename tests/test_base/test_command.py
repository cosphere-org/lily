
import json
from contextlib import ContextDecorator
from unittest.mock import Mock

from django.test import TestCase
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError
from django.contrib.auth.models import User
from django_fake_model import models as fake_models
from django.db import models, transaction
import pytest

from lily.base.command import command, HTTPCommands
from lily.base.access import Access
from lily.base.meta import Meta, Domain
from lily.base.input import Input
from lily.base.output import Output
from lily.base import serializers, parsers
from lily.base.events import EventFactory


event = EventFactory()


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


class GenericCommands(HTTPCommands):

    @command(
        name='GET_IT',
        meta=Meta(
            title='get',
            description='get it...',
            domain=Domain(id='get', name='get')),
    )
    def get(self, request):

        status_code = int(request.GET['status_code'])

        raise self.event.Generic(
            status_code=status_code,
            content=json.dumps({
                '@event': 'FOUND_IT',
                '@type': 'what',
                'hi': status_code,
            }))


class HttpCommands(HTTPCommands):

    @command(
        name='HTTP_IT',
        meta=Meta(
            title='http',
            description='http it...',
            domain=Domain(id='http', name='http')),
    )
    def get(self, request):

        return HttpResponse('hello world')


@FakeClient.fake_me
class TestCommands(HTTPCommands):

    class BodyParser(parsers.Parser):

        name = parsers.CharField()

        age = parsers.IntegerField()

    class ClientSerializer(serializers.ModelSerializer):

        _type = 'client'

        card_id = serializers.SerializerMethodField()

        def get_access(self, instance):
            return [(TestCommands.put, True)]

        class Meta:
            model = FakeClient
            fields = ('name', 'card_id')

        def get_card_id(self, instance):
            return 190

    class SimpleSerializer(serializers.Serializer):
        _type = 'simple'

        amount = serializers.IntegerField()

    @command(
        name='MAKE_IT',
        meta=Meta(
            title='hi there',
            description='it is made for all',
            domain=Domain(id='test', name='test management')),
        input=Input(body_parser=BodyParser),
        output=Output(serializer=ClientSerializer),
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
        output=Output(serializer=ClientSerializer))
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
        is_atomic=True)
    def delete(self, request):

        self.some_stuff()

        raise self.event.Executed(event='ATOMIC', context=request, data={})

    def some_stuff(self):
        pass


class DoAndGoCommands(HTTPCommands):

    @command(
        name='DO_AND_GO',
        meta=Meta(
            title='do and go',
            domain=Domain(id='test', name='test management')),
        access=Access(access_list=['PREMIUM'])
    )
    def post(self, request):

        raise self.event.Redirect(
            'DONE_SO_GO',
            redirect_uri='http://go.there.org')


@FakeClient.fake_me
class BrokenSerializerCommands(HTTPCommands):

    class ClientSerializer(serializers.Serializer):

        _type = 'client'

        card_id = serializers.SerializerMethodField()

        def get_card_id(self, instance):
            raise EventFactory.AccessDenied('GO_AWAY')

    @command(
        name='BREAK_SERIALIZER',
        meta=Meta(
            title='break it',
            domain=Domain(id='test', name='test management')),
        output=Output(serializer=ClientSerializer),
        access=Access(access_list=['PREMIUM', 'SUPER_PREMIUM'])
    )
    def post(self, request):
        raise self.event.Executed(
            event='NEVER_REACH_IT',
            instance=FakeClient(name="Jake"))


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

        c = TestCommands()

        response = c.post(request, 11)

        assert response.status_code == 200
        assert to_json(response) == {
            '@type': 'client',
            '@event': 'MADE_IT',
            '@access': {
                'BREAK': True,
            },
            'name': 'Jake',
            'card_id': 190,
        }

    #
    # REDIRECT
    #
    def test_redirect(self):

        request = Mock(META=get_auth_headers(11, 'PREMIUM'))

        response = DoAndGoCommands().post(request)

        assert response.status_code == 303
        assert to_json(response) == {
            '@authorizer': {'account_type': 'PREMIUM', 'user_id': 11},
            '@event': 'DONE_SO_GO',
            '@type': 'error',
        }

    #
    # BROKEN SERIALIZER
    #
    def test_exception_from_serializer(self):

        request = Mock(META=get_auth_headers(11, 'PREMIUM'))

        response = BrokenSerializerCommands().post(request)

        assert response.status_code == 403
        assert to_json(response) == {
            '@authorizer': {'account_type': 'PREMIUM', 'user_id': 11},
            '@event': 'GO_AWAY',
            '@type': 'error',
        }

    #
    # AUTHORIZATION
    #
    def test_access_denied__missing_headers(self):

        request = Request()
        request.body = dump_to_bytes({"name": "John", "age": 81})
        request.META = {}
        c = TestCommands()

        response = c.post(request, 12)

        assert response.status_code == 403
        assert to_json(response) == {
            '@type': 'error',
            '@event': 'ACCESS_DENIED',
        }

    def test_no_authorization(self):

        request = Request()
        request.body = dump_to_bytes({"name": "John", "age": 81})
        request.META = {}
        c = TestCommands()

        response = c.get(request)

        assert response.status_code == 200

    #
    # CONF
    #
    def test_conf__context_attached_to_the_request(self):

        u = User.objects.create_user(username='jacky')
        request = Request()
        request.body = dump_to_bytes({"name": "John", "age": 81})
        request.META = get_auth_headers(u.id, 'SUPER_PREMIUM')
        c = TestCommands()

        c.post(request, 15)

        assert request._lily_context.command_name == 'MAKE_IT'
        assert request._lily_context.correlation_id is not None

    def test_conf__is_saved_on_function(self):

        source = TestCommands.post.command_conf.pop('source')
        assert TestCommands.post.command_conf == {
            'name': 'MAKE_IT',
            'method': 'post',
            'meta': Meta(
                title='hi there',
                description='it is made for all',
                domain=Domain(id='test', name='test management')),
            'access': Access(
                access_list=['PREMIUM', 'SUPER_PREMIUM']),
            'input': Input(body_parser=TestCommands.BodyParser),
            'output': Output(serializer=TestCommands.ClientSerializer),
            'is_atomic': False,
            'fn': TestCommands.post.command_conf['fn'],
        }

        assert source.filepath == '/tests/test_base/test_command.py'
        assert source.start_line == 117
        assert source.end_line == 131

    #
    # INPUT
    #
    def test_input__body_parsing(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            body=dump_to_bytes({'name': 'John', 'age': 81}),
            META=get_auth_headers(u.id))
        c = TestCommands()

        response = c.post(request, 19)

        assert request.input.body == {'name': 'John', 'age': 81}
        assert response.status_code == 200

    #
    # RESPONSE VALIDATION
    #
    def test_response_valid(self):

        u = User.objects.create_user(username='jacky')
        meta = get_auth_headers(u.id)
        meta['SERVER_NAME'] = 'testserver'
        request = Mock(
            body=dump_to_bytes({'amount': 81}),
            log_authorizer={
                'user_id': u.id,
            },
            META=meta)
        c = TestCommands()

        response = c.put(request)

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
            log_authorizer={
                'user_id': u.id,
            },
            META=meta)
        c = TestCommands()

        response = c.put(request)

        assert response.status_code == 400
        assert to_json(response) == {
            '@authorizer': {
                'user_id': u.id,
            },
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
            log_authorizer={
                'user_id': u.id,
            },
            META=get_auth_headers(u.id))
        c = TestCommands()
        self.mocker.patch.object(c, 'some_stuff').side_effect = [
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
        response = c.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'DATABASE_ERROR_OCCURRED',
            '@type': 'error',
            '@authorizer': {
                'user_id': u.id,
            },

        }
        assert isinstance(AtomicContext.exception, DatabaseError)

        # -- generic error
        response = c.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'GENERIC_ERROR_OCCURRED',
            '@type': 'error',
            'errors': ['hi there'],
            '@authorizer': {
                'user_id': u.id,
            },
        }
        assert isinstance(AtomicContext.exception, Exception)

        # -- not a success exception
        response = c.delete(request)

        assert response.status_code == 400
        assert to_json(response) == {
            '@event': 'ERROR!',
            '@type': 'error',
            '@authorizer': {
                'user_id': u.id,
            },
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
        c = TestCommands()
        self.mocker.patch.object(c, 'some_stuff').side_effect = [

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
        response = c.delete(request)

        assert response.status_code == 200
        assert to_json(response) == {'@event': 'SUCCESS!', '@type': 'empty'}
        assert AtomicContext.exception is None

        # -- created exception
        response = c.delete(request)

        assert response.status_code == 201
        assert to_json(response) == {'@event': 'CREATED!', '@type': 'empty'}
        assert AtomicContext.exception is None

    #
    # GENERIC ERRORS
    #
    def test_validation_error(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            log_authorizer={
                'user_id': u.id,
            },
            META=get_auth_headers(u.id))
        c = TestCommands()
        self.mocker.patch.object(c, 'some_stuff').side_effect = (
            ValidationError({'field': ['is broken']}))

        response = c.delete(request)

        assert response.status_code == 400
        assert to_json(response) == {
            '@event': 'BODY_JSON_DID_NOT_PARSE',
            '@type': 'error',
            '@authorizer': {
                'user_id': u.id,
            },
            'errors': {'field': ['is broken']},
        }

    def test_does_not_exist(self):

        u = User.objects.create_user(username='jacky')
        request = Mock(
            log_authorizer={
                'user_id': u.id,
            },
            META=get_auth_headers(u.id))
        c = TestCommands()
        self.mocker.patch.object(c, 'some_stuff').side_effect = (
            lambda: User.objects.get(id=4930))

        response = c.delete(request)

        assert response.status_code == 404
        assert to_json(response) == {
            '@event': 'COULD_NOT_FIND_USER',
            '@type': 'error',
            '@authorizer': {
                'user_id': u.id,
            },
        }

    def test_multiple_objects_returned(self):

        u = User.objects.create_user(username='jacky')
        u = User.objects.create_user(username='jacks')
        request = Mock(
            log_authorizer={
                'user_id': u.id,
            },
            META=get_auth_headers(u.id))
        c = TestCommands()
        self.mocker.patch.object(c, 'some_stuff').side_effect = (
            lambda: User.objects.get(username__contains='jack'))

        response = c.delete(request)

        assert response.status_code == 500
        assert to_json(response) == {
            '@event': 'FOUND_MULTIPLE_INSTANCES_OF_USER',
            '@type': 'error',
            '@authorizer': {
                'user_id': u.id,
            },
        }

    #
    # GENERIC RESPONSE
    #
    def test_generic_response(self):

        # -- 201
        request = Mock(GET={'status_code': '201'}, META={})
        c = GenericCommands()

        response = c.get(request)

        assert response.status_code == 201
        assert to_json(response) == {
            '@event': 'FOUND_IT',
            '@type': 'what',
            'hi': 201,
        }

        # -- 404
        request = Mock(GET={'status_code': '404'}, META={})
        c = GenericCommands()

        response = c.get(request)

        assert response.status_code == 404
        assert to_json(response) == {
            '@event': 'FOUND_IT',
            '@type': 'what',
            'hi': 404,
        }

    #
    # HTTP RESPONSE
    #
    def test_http_response(self):

        # -- 404
        request = Mock(GET={'status_code': '404'}, META={})
        c = HttpCommands()

        response = c.get(request)

        assert response.status_code == 200
        assert response.content == b'hello world'
        assert response.get('Content-Type') == 'text/html; charset=utf-8'

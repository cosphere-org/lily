
from django.test import TestCase
from django.http import HttpResponse
import pytest
from unittest.mock import Mock, call

from lily.base.events import EventFactory


class GenericExceptionTestCase(TestCase):

    def test_init(self):

        e = EventFactory.Generic(status_code=401, content='{"hello":"there"}')

        assert e.status_code == 401
        assert e.content == '{"hello":"there"}'

    def test_extend(self):

        e = EventFactory.Generic(status_code=401, content='{"hello":"there"}')
        extended = e.extend(method='POST', path='/hi/there')

        assert extended.method == 'POST'
        assert extended.path == '/hi/there'
        assert isinstance(extended, EventFactory.Generic)

    def test_log(self):

        e = EventFactory.Generic(status_code=401, content='{"hello":"there"}')
        e.logger = Mock()

        e.extend(method='POST', path='/hi/there').log()

        assert e.logger.info.call_args_list == (
            [call('[POST /hi/there] -> 401')])

    def test_response(self):
        e = EventFactory.Generic(status_code=401, content='{"hello":"there"}')

        response = e.response()

        assert isinstance(response, HttpResponse)
        assert response.status_code == 401
        assert response.content == b'{"hello":"there"}'


class ContextTestCase(TestCase):

    def test_constructor(self):

        c = EventFactory.Context(user_id=12, email='a@p.a', origin='here')

        assert c.data['user_id'] == 12
        assert c.data['email'] == 'a@p.a'
        assert c.data['origin'] == 'here'

    def test_is_empty(self):

        assert EventFactory.Context().is_empty() is True
        assert EventFactory.Context(user_id=11).is_empty() is False
        assert EventFactory.Context(origin='here').is_empty() is False
        assert EventFactory.Context(email='here@here').is_empty() is False


class BaseSuccessExceptionTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def test_create_empty__defaults(self):

        e = EventFactory.BaseSuccessException()

        assert e.data == {}
        assert e.context == EventFactory.Context()
        assert e.event is None
        assert e.instance is None

    def test_extend(self):

        context = Mock()
        e = EventFactory.BaseSuccessException()
        prev_context = e.context

        e.extend(event='HI', context=context)

        assert e.event == 'HI'
        assert e.context == context
        assert e.context != prev_context

    def test_log__user_id_in_context(self):

        dumps = self.mocker.patch('lily.base.events.json.dumps')
        dumps.return_value = '{XX}'
        e = EventFactory.BaseSuccessException(
            context=Mock(log_authorizer={'user_id': 12}), event='HELLO')
        logger = self.mocker.patch.object(e, 'logger')

        e.log()

        assert logger.info.call_args_list == [call('HELLO: {XX}')]
        assert dumps.call_args_list == [
            call({'@authorizer': {'user_id': 12}, '@event': 'HELLO'})]

    def test_log__no_user_id_in_context(self):

        dumps = self.mocker.patch('lily.base.events.json.dumps')
        dumps.return_value = '{XX}'
        logger = Mock()
        e = EventFactory.BaseSuccessException(
            context=EventFactory.Context(), event='HELLO')
        logger = self.mocker.patch.object(e, 'logger')

        e.log()

        assert logger.info.call_args_list == [call('HELLO: {XX}')]
        assert dumps.call_args_list == [call({'@event': 'HELLO'})]


@pytest.mark.parametrize(
    'exception, expected_status_code', [

        #
        # SUCCESS RESPONSES
        #
        (EventFactory.Executed, 200),

        (EventFactory.Created, 201),
        (EventFactory.Read, 200),
        (EventFactory.Updated, 200),
        (EventFactory.Deleted, 200),

        (EventFactory.BulkCreated, 201),
        (EventFactory.BulkRead, 200),
        (EventFactory.BulkUpdated, 200),
        (EventFactory.BulkDeleted, 200),

        #
        # ERROR RESPONSES
        #
        (EventFactory.BrokenRequest, 400),
        (EventFactory.AuthError, 401),
        (EventFactory.AccessDenied, 403),
        (EventFactory.DoesNotExist, 404),
        (EventFactory.Conflict, 409),
        (EventFactory.ServerError, 500),
    ])
def test_response_classes(exception, expected_status_code):

    assert exception.response_class.status_code == expected_status_code

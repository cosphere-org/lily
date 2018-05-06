# -*- coding: utf-8 -*-

from django.test import TestCase
import pytest
from mock import Mock, call

from lily.base.events import EventFactory


class ContextTestCase(TestCase):

    def test_constructor(self):

        c = EventFactory.Context(user_id=12, email='a@p.a', origin='here')

        assert c.user_id == 12
        assert c.email == 'a@p.a'
        assert c.origin == 'here'

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
        logger = Mock()
        EventFactory.BaseSuccessException.logger = logger
        e = EventFactory.BaseSuccessException(
            context=Mock(user_id=12), event='HELLO')

        e.log()

        assert logger.info.call_args_list == [call('HELLO: {XX}')]
        assert dumps.call_args_list == [
            call({'user_id': 12, '@event': 'HELLO'})]

    def test_log__no_user_id_in_context(self):

        dumps = self.mocker.patch('lily.base.events.json.dumps')
        dumps.return_value = '{XX}'
        logger = Mock()
        EventFactory.BaseSuccessException.logger = logger
        e = EventFactory.BaseSuccessException(
            context=EventFactory.Context(), event='HELLO')

        e.log()

        assert logger.info.call_args_list == [call('HELLO: {XX}')]
        assert dumps.call_args_list == [
            call({'user_id': 'anonymous', '@event': 'HELLO'})]


class BaseErrorExceptionTestCase(TestCase):

    def test_create_empty__defaults(self):
        pass

    def test_context_attributes_added(self):
        pass


@pytest.mark.parametrize(
    'exception, expected_status_code', [

        #
        # SUCCESS RESPONSES
        #
        (EventFactory.Executed, 200),
        (EventFactory.Created, 201),
        (EventFactory.Success, 200),
        (EventFactory.Read, 200),
        (EventFactory.Listed, 200),
        (EventFactory.Updated, 200),
        (EventFactory.Deleted, 200),

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

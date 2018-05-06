# -*- coding: utf-8 -*-

import logging
from django.test import TestCase
from django.contrib.auth.models import User
from mock import Mock
import pytest

from lily.base import parsers
from lily.base.events import EventFactory
from lily.base.input import Input
from .test_parsers import RequestGet


logger = logging.getLogger()


event = EventFactory(logger)


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
            email=None,
            origin=None,
            user_id=902)

        try:
            input.parse_query(request)

        except EventFactory.BrokenRequest as e:
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

        request = Mock(
            body='{not json',
            email=None,
            origin=None,
            user_id=902)

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
            body=b'{"title": "hi there", "amount": 20}',
            user_id=902,
            email=None,
            origin=None)

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
        request = Mock(
            body=b'{"amount": 19}',
            user_id=902,
            email=None,
            origin=None)

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

        request = Mock(
            body=b'{"title": "hi", "amount": 19}',
            origin=None,
            email=None,
            user_id=190)

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

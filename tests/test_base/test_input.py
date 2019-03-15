
from django.test import TestCase
from django.contrib.auth.models import User
from mock import Mock
import pytest

from lily.base import parsers
from lily.base.events import EventFactory
from lily.base.input import Input
from .test_parsers import RequestGet


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
        query_parser, body_parser = Mock(), Mock()
        request = Mock()

        # -- both query and body parsers
        i = Input(
            query_parser=query_parser, body_parser=body_parser)
        i.parse(request, command_name='MAKE_IT')

        assert parse_body.call_count == 1
        assert parse_query.call_count == 1

    #
    # PARSE_QUERY
    #
    def test_parse_query__all_ok(self):
        class QueryParser(parsers.QueryParser):
            title = parsers.CharField()
            prices = parsers.ListField(child=parsers.IntegerField())

        input = Input(query_parser=QueryParser)

        request = Mock(
            GET=RequestGet(title=['hi there'], prices=[67, 89, 11]),
            user_id=902)

        data = input.parse_query(request)

        assert data == {'title': 'hi there', 'prices': [67, 89, 11]}

    def test_parse_query__multiple_parsers(self):
        class AParser(parsers.QueryParser):
            title = parsers.CharField()
            prices = parsers.ListField(child=parsers.IntegerField())

        class BParser(parsers.QueryParser):
            title = parsers.CharField()
            quantity = parsers.IntegerField()

        class CParser(AParser, BParser):
            pass

        input = Input(query_parser=CParser)

        request = Mock(
            GET=RequestGet(
                title=['hi there'],
                prices=[67, 89, 11],
                quantity=[190]),
            user_id=902)

        data = input.parse_query(request)

        assert data == {
            'title': 'hi there',
            'prices': [67, 89, 11],
            'quantity': 190,
        }

    def test_parse_query__all_missing(self):
        class QueryParser(parsers.QueryParser):
            title = parsers.CharField()
            prices = parsers.ListField(child=parsers.IntegerField())

        input = Input(query_parser=QueryParser)

        request = Mock(
            GET=RequestGet(),
            origin=None,
            log_access={
                'user_id': 902,
            })

        try:
            input.parse_query(request)

        except EventFactory.BrokenRequest as e:
            assert e.event == 'QUERY_DID_NOT_VALIDATE'

        else:
            raise AssertionError

    def test_parse_query__event__query_did_not_validate(self):

        class QueryParser(parsers.QueryParser):
            title = parsers.CharField()

            prices = parsers.ListField(child=parsers.IntegerField())

        input = Input(query_parser=QueryParser)

        request = Mock(
            GET=RequestGet(title=['hi there'], prices=['what']),
            origin=None,
            log_access={
                'user_id': 902,
            })

        try:
            input.parse_query(request)

        except EventFactory.BrokenRequest as e:
            assert e.data == {
                '@type': 'error',
                '@event': 'QUERY_DID_NOT_VALIDATE',
                '@access': {
                    'user_id': 902,
                },
                'errors': {
                    'prices': ['A valid integer is required.'],
                },
            }

        else:
            raise AssertionError

    #
    # PARSE_BODY
    #
    def _prepare_body_parser(self):
        class BodyParser(parsers.BodyParser):
            title = parsers.CharField()
            amount = parsers.IntegerField(max_value=19)

        input = Input(body_parser=BodyParser)

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
            origin=None,
            log_access={
                'user_id': 902,
            })

        try:
            input.parse_body(request, command_name='MAKE_IT')

        except EventFactory.BrokenRequest as error:
            assert error.event == 'BODY_JSON_DID_NOT_PARSE'
            assert error.data == {
                '@type': 'error',
                '@event': 'BODY_JSON_DID_NOT_PARSE',
                '@access': {
                    'user_id': 902,
                },
            }
            assert error.is_critical

        else:
            raise AssertionError('didn\'t raise error!')

    def test_parse_body__invalid_payload(self):
        input = self._prepare_body_parser()

        # -- amount too big error
        request = Mock(
            body=b'{"title": "hi there", "amount": 20}',
            log_access={
                'user_id': 902,
            },
            origin=None)

        try:
            input.parse_body(request, command_name='MAKE_IT')

        except EventFactory.BrokenRequest as error:
            assert error.event == 'BODY_DID_NOT_VALIDATE'
            assert error.data == {
                '@type': 'error',
                '@event': 'BODY_DID_NOT_VALIDATE',
                '@access': {
                    'user_id': 902,
                },
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
            origin=None,
            log_access={
                'user_id': 902,
            })

        try:
            input.parse_body(request, command_name='MAKE_IT')

        except EventFactory.BrokenRequest as error:
            assert error.event == 'BODY_DID_NOT_VALIDATE'
            assert error.data == {
                '@type': 'error',
                '@event': 'BODY_DID_NOT_VALIDATE',
                '@access': {
                    'user_id': 902,
                },
                'errors': {
                    'title': ['This field is required.']
                }
            }
            assert not error.is_critical

        else:
            raise AssertionError('didn\'t raise error!')

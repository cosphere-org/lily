# -*- coding: utf-8 -*-

from django.test import TestCase

from lily.base import parsers


class RequestGet(dict):

    def getlist(self, name, alternative=None):
        return self.get(name, alternative)

    # -- RequestGet should behave as request.GET
    def __getitem__(self, name):
        return super(RequestGet, self).__getitem__(name)[0]


class QueryParserTestCases(TestCase):

    def test_init__boolean_field(self):
        class QueryParser(parsers.QueryParser):
            is_ready = parsers.BooleanField()

        cases = [
            (['true'], True),
            (['True'], True),
            (['t'], True),
            (['T'], True),
            (['false'], False),
            (['False'], False),
            (['f'], False),
            (['F'], False),
        ]
        for input_value, expected in cases:
            parser = QueryParser(data=RequestGet(is_ready=input_value))

            assert parser.is_valid() is True
            assert parser.data == {'is_ready': expected}

    def test_init__list_boolean_field(self):
        class QueryParser(parsers.QueryParser):
            is_ready = parsers.ListField(child=parsers.BooleanField())

        cases = [
            ([], []),
            (['true'], [True]),
            (['True', 'False'], [True, False]),
            (['t', 'f', 'true'], [True, False, True]),
            (['T', 'F', 'f'], [True, False, False]),
        ]
        for input_value, expected in cases:
            parser = QueryParser(data=RequestGet(is_ready=input_value))

            assert parser.is_valid() is True
            assert parser.data == {'is_ready': expected}

    def test_init__number_fields(self):
        class QueryParser(parsers.QueryParser):
            price = parsers.IntegerField(default=12)
            value = parsers.FloatField(default=18.5)

        cases = [
            (([1], [2.3]), (1, 2.3)),
            ((['1'], ['2.3']), (1, 2.3)),
            ((['11'], ['122']), (11, 122.0)),
            (([], []), (12, 18.5)),
        ]
        for input_value, expected in cases:
            price, value = input_value
            expected_price, expected_value = expected
            parser = QueryParser(data=RequestGet(price=price, value=value))

            assert parser.is_valid() is True
            assert parser.data == {
                'price': expected_price, 'value': expected_value}

    def test_init__list_number_fields(self):
        class QueryParser(parsers.QueryParser):
            price = parsers.ListField(child=parsers.IntegerField(default=12))
            value = parsers.ListField(child=parsers.FloatField(default=18.5))

        cases = [
            (([1], [2.3]), ([1], [2.3])),
            ((['1', '-9'], ['2.3', 78, '6.78']), ([1, -9], [2.3, 78.0, 6.78])),
        ]
        for input_value, expected in cases:
            price, value = input_value
            expected_price, expected_value = expected
            parser = QueryParser(data=RequestGet(price=price, value=value))

            assert parser.is_valid() is True
            assert parser.data == {
                'price': expected_price, 'value': expected_value}

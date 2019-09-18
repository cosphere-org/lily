
from django.test import TestCase

from lily.base import parsers


class RequestGet(dict):

    def getlist(self, name, alternative=None):
        return self.get(name, alternative)

    # -- RequestGet should behave as request.GET
    def __getitem__(self, name):
        return super(RequestGet, self).__getitem__(name)[0]


class QueryParserTestCase(TestCase):

    def test_init__boolean_field(self):
        class QueryParser(parsers.Parser):
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
            parser = QueryParser.as_query_parser(
                data=RequestGet(is_ready=input_value))

            assert parser.is_valid() is True
            assert parser.data == {'is_ready': expected}

    def test_init__list_boolean_field(self):
        class QueryParser(parsers.Parser):

            is_ready = parsers.ListField(child=parsers.BooleanField())

        cases = [
            ([], []),
            (['true'], [True]),
            (['True', 'False'], [True, False]),
            (['t', 'f', 'true'], [True, False, True]),
            (['T', 'F', 'f'], [True, False, False]),
        ]
        for input_value, expected in cases:
            parser = QueryParser.as_query_parser(
                data=RequestGet(is_ready=input_value))

            assert parser.is_valid() is True
            assert parser.data == {'is_ready': expected}

    def test_init__number_fields(self):
        class QueryParser(parsers.Parser):
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
            parser = QueryParser.as_query_parser(
                data=RequestGet(price=price, value=value))

            assert parser.is_valid() is True
            assert parser.data == {
                'price': expected_price, 'value': expected_value}

    def test_init__list_number_fields(self):
        class QueryParser(parsers.Parser):
            price = parsers.ListField(child=parsers.IntegerField(default=12))
            value = parsers.ListField(child=parsers.FloatField(default=18.5))

        cases = [
            (([1], [2.3]), ([1], [2.3])),
            ((['1', '-9'], ['2.3', 78, '6.78']), ([1, -9], [2.3, 78.0, 6.78])),
        ]
        for input_value, expected in cases:
            price, value = input_value
            expected_price, expected_value = expected
            parser = QueryParser.as_query_parser(
                data=RequestGet(price=price, value=value))

            assert parser.is_valid() is True
            assert parser.data == {
                'price': expected_price, 'value': expected_value}

    def test_init__data_is_optional(self):
        class QueryParser(parsers.Parser):
            is_ready = parsers.BooleanField()

        # -- no error is raised
        QueryParser.as_query_parser()


class PageQueryParstCase(TestCase):

    def test_parse(self):

        parser = parsers.PageParser.as_query_parser(
            data={'offset': '11', 'limit': 456})

        assert parser.is_valid() is True
        assert parser.data == {'offset': 11, 'limit': 456}

    def test_parse__defaults(self):

        parser = parsers.PageParser.as_query_parser(data={})

        assert parser.is_valid() is True
        assert parser.data == {'offset': 0, 'limit': 100}

    def test_parse__invalid(self):

        parser = parsers.PageParser.as_query_parser(
            data={'offset': 'HEY', 'limit': 'X'})

        assert parser.is_valid() is False
        assert parser.errors == {
            'limit': ['A valid integer is required.'],
            'offset': ['A valid integer is required.'],
        }


class FullTextSearchParserTestCase(TestCase):

    def test_parse(self):

        parser = parsers.FullTextSearchParser.as_query_parser(
            data={'query': 'hello'})

        assert parser.is_valid() is True
        assert parser.data == {'query': 'hello'}

    def test_parse__defaults(self):

        parser = parsers.FullTextSearchParser.as_query_parser(data={})

        assert parser.is_valid() is True
        assert parser.data == {'query': None}

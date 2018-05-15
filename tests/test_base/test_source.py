# -*- coding: utf-8 -*-

from django.test import TestCase

from lily.base.source import Source, SourceSerializer


class SourceTestCase(TestCase):

    def test_constructor(self):

        def fn():
            a = 1
            b = a
            return b

        source = Source(fn)

        assert source.filepath == '/tests/test_base/test_source.py'
        assert source.start_line == 12
        assert source.end_line == 15


class SourceSerializerTestCase(TestCase):

    def test_serialization(self):

        def fn():
            a = 1
            return a

        source = Source(fn)

        assert SourceSerializer(source).data == {
            '@type': 'source',
            'filepath': '/tests/test_base/test_source.py',
            'start_line': 28,
            'end_line': 30,
        }

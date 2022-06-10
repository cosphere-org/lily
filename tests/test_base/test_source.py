
import os

from django.test import TestCase
import pytest

from lily.base.source import Source, SourceSerializer


class SourceTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initifixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        self.mocker.patch('lily.base.source.get_project_path').return_value = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', '..')

    def test_constructor(self):

        def fn():
            a = 1
            b = a
            return b

        source = Source(fn)

        assert source.filepath.endswith('/tests/test_base/test_source.py')
        assert source.start_line == 22
        assert source.end_line == 25


class SourceSerializerTestCase(TestCase):

    def test_serialization(self):

        def fn():
            a = 1
            return a

        source = Source(fn)

        assert SourceSerializer(source).data == {
            '@type': 'source',
            'filepath': '/tests/test_base/test_source.py',
            'start_line': 38,
            'end_line': 40,
        }

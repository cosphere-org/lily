
import os

from django.test import TestCase
import pytest

from lily.base.source import Source, SourceSerializer


class SourceTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initifixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        class ConfigMock:

            @classmethod
            def get_project_path(cls):
                return os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    '..')

        self.mocker.patch('base.source.Config', ConfigMock)

    def test_constructor(self):

        def fn():
            a = 1
            b = a
            return b

        source = Source(fn)

        assert source.filepath == '/tests/test_base/test_source.py'
        assert source.start_line == 30
        assert source.end_line == 33


class SourceSerializerTestCase(TestCase):

    def test_serialization(self):

        def fn():
            a = 1
            return a

        source = Source(fn)

        assert SourceSerializer(source).data == {
            '@type': 'source',
            'filepath': '/tests/test_base/test_source.py',
            'start_line': 46,
            'end_line': 48,
        }

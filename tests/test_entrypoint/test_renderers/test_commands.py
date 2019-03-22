
import json
from collections import OrderedDict
from unittest.mock import Mock

from django.test import TestCase
import pytest

from lily.entrypoint.renderers.commands import CommandsRenderer
from lily.entrypoint.renderers.base import BaseRenderer
from lily import Input, Output, Meta, Domain, Access, Source


def fn():
    pass


class CommandsRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

        examples = self.tmpdir.join('examples.json')
        examples.write('{}')
        self.examples_filepath = str(examples)
        self.mocker.patch(
            'lily.entrypoint.renderers.commands.get_examples_filepath'
        ).return_value = self.examples_filepath

    def test_render(self):
        renderer = self.mocker.patch(
            'lily.entrypoint.renderers.commands.SchemaRenderer')
        serialize = Mock()
        renderer.return_value.render.return_value = Mock(serialize=serialize)
        serialize.side_effect = [
            {'output': 'schema'},
            {'query': 'schema'},
            {'body': 'schema'},
        ]

        meta = Meta(
            title='hi',
            description='ho',
            domain=Domain(id='h', name='hh'))
        access = Access(access_list=['EVERYONE'], is_private=True)
        source = Source(fn)
        self.mocker.patch.object(BaseRenderer, 'render').return_value = {
            'READ_CARD': {
                'method': 'get',
                'path_conf': {
                    'path': '/hi',
                    'pattern': '/hi',
                    'parameters': [],
                },
                'meta': meta,
                'access': access,
                'input': Input(query_parser=Mock(), body_parser=Mock()),
                'output': Output(serializer=Mock()),
                'source': source,
            }
        }

        assert CommandsRenderer().render() == {
            'READ_CARD': {
                'access': access,
                'meta': meta,
                'method': 'get',
                'path_conf': {
                    'parameters': [],
                    'path': '/hi',
                },
                'schemas': {
                    'input_body': {'body': 'schema'},
                    'input_query': {'query': 'schema'},
                    'output': {'output': 'schema'},
                },
                'source': source,
                'examples': {},
            }
        }

    def test_render__many_commands(self):
        renderer = self.mocker.patch(
            'lily.entrypoint.renderers.commands.SchemaRenderer')
        serialize = Mock()
        renderer.return_value.render.return_value = Mock(serialize=serialize)
        serialize.side_effect = [
            {'output': 'read.schema'},
            {'query': 'read.schema'},
            {'body': 'read.schema'},
            {'output': 'delete.schema'},
            {'query': 'delete.schema'},
            {'body': 'delete.schema'},

        ]

        meta = Meta(
            title='hi',
            description='ho',
            domain=Domain(id='h', name='hh'))
        access = Access(access_list=['EVERYONE'], is_private=True)
        source = Source(fn)
        self.mocker.patch.object(
            BaseRenderer,
            'render'
        ).return_value = OrderedDict([
            (
                'READ_CARD',
                {
                    'method': 'get',
                    'path_conf': {
                        'path': '/hi',
                        'pattern': '/hi',
                        'parameters': [],
                    },
                    'meta': meta,
                    'access': access,
                    'input': Input(query_parser=Mock(), body_parser=Mock()),
                    'output': Output(serializer=Mock()),
                    'source': source,
                },
            ),
            (
                'DELETE_TASK',
                {
                    'method': 'delete',
                    'path_conf': {
                        'path': '/hi/{id}',
                        'pattern': '/hi/(?P<id>\\d+)',
                        'parameters': [{'name': 'id', 'type': 'integer'}],
                    },
                    'meta': meta,
                    'access': access,
                    'input': Input(query_parser=Mock(), body_parser=Mock()),
                    'output': Output(serializer=Mock()),
                    'source': source,
                }
            )])

        assert CommandsRenderer().render() == {
            'READ_CARD': {
                'access': access,
                'meta': meta,
                'method': 'get',
                'path_conf': {
                    'parameters': [],
                    'path': '/hi',
                },
                'schemas': {
                    'input_body': {'body': 'read.schema'},
                    'input_query': {'query': 'read.schema'},
                    'output': {'output': 'read.schema'},
                },
                'source': source,
                'examples': {},
            },
            'DELETE_TASK': {
                'access': access,
                'meta': meta,
                'method': 'delete',
                'path_conf': {
                    'path': '/hi/{id}',
                    'parameters': [{'name': 'id', 'type': 'integer'}],
                },
                'schemas': {
                    'input_body': {'body': 'delete.schema'},
                    'input_query': {'query': 'delete.schema'},
                    'output': {'output': 'delete.schema'},
                },
                'source': source,
                'examples': {},
            },
        }

    def test_render__with_examples(self):
        renderer = self.mocker.patch(
            'lily.entrypoint.renderers.commands.SchemaRenderer')
        serialize = Mock()
        renderer.return_value.render.return_value = Mock(serialize=serialize)
        serialize.side_effect = [
            {'output': 'schema'},
            {'query': 'schema'},
            {'body': 'schema'},
        ]

        meta = Meta(
            title='hi',
            description='ho',
            domain=Domain(id='h', name='hh'))
        access = Access(access_list=['EVERYONE'], is_private=True)
        source = Source(fn)
        self.mocker.patch.object(BaseRenderer, 'render').return_value = {
            'READ_CARD': {
                'method': 'get',
                'path_conf': {
                    'path': '/hi',
                    'pattern': '/hi',
                    'parameters': [],
                },
                'meta': meta,
                'access': access,
                'input': Input(query_parser=Mock(), body_parser=Mock()),
                'output': Output(serializer=Mock()),
                'source': source,
            }
        }

        with open(self.examples_filepath, 'w') as f:
            f.write(json.dumps({
                'READ_CARD': {
                    '200 (OK)': {
                        'request': {
                            'path': '/hi',
                            'parameters': {},
                        },
                    },
                },
            }))

        assert CommandsRenderer().render() == {
            'READ_CARD': {
                'access': access,
                'meta': meta,
                'method': 'get',
                'path_conf': {
                    'parameters': [],
                    'path': '/hi',
                },
                'schemas': {
                    'input_body': {'body': 'schema'},
                    'input_query': {'query': 'schema'},
                    'output': {'output': 'schema'},
                },
                'source': source,
                'examples': {
                    '200 (OK)': {
                        'request': {
                            'path': '/hi',
                            'parameters': {},
                        },
                    },
                },
            }
        }

    def test_render__no_commands(self):
        self.mocker.patch.object(BaseRenderer, 'render').return_value = {}

        assert CommandsRenderer().render() == {}

    #
    # get_examples
    #
    def test_get_examples(self):
        renderer = CommandsRenderer()
        renderer.examples = {
            'COMMAND_A': {
                '200 (OK)': {
                    'request': {
                        'path': '/a/a/'
                    },
                    'response': {
                        'content': 'hi',
                    }
                },
            },
            'COMMAND_B': {
                'other': 'stuff',
            }
        }

        assert renderer.get_examples('COMMAND_A', r'/a/a/') == {
            '200 (OK)': {
                'request': {
                    'path': '/a/a/',
                    'parameters': {},
                },
                'response': {
                    'content': 'hi',
                },
            }
        }

    def test_get_examples__no_examples(self):
        renderer = CommandsRenderer()
        renderer.examples = {
            'COMMAND_A': {'hi': 'there'},
        }

        assert renderer.get_examples('COMMAND_B', r'') == {}

    def test_get_examples__with_pamaterized_paths(self):
        renderer = CommandsRenderer()
        renderer.examples = {
            'COMMAND_A': {
                '200 (OK)': {
                    'request': {
                        'path': '/a/12/b/there'
                    },
                    'response': {
                        'content': 'hi',
                    }
                },
            },
            'COMMAND_B': {
                'other': 'stuff',
            }
        }

        assert renderer.get_examples(
            'COMMAND_A',
            r'/a/(?P<id>\d+)/b/(?P<name>\w+)'
        ) == {
            '200 (OK)': {
                'request': {
                    'path': '/a/12/b/there',
                    'parameters': {
                        'id': '12',
                        'name': 'there',
                    },
                },
                'response': {
                    'content': 'hi',
                },
            }
        }

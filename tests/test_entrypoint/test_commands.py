
from copy import deepcopy

from django.test import TestCase
from django.urls import reverse
import pytest
from mock import Mock, call

from lily.base.test import Client
from lily.entrypoint.commands import CommandSerializer
from tests import EntityGenerator


eg = EntityGenerator()


class EntryPointCommandsTestCase(TestCase):

    uri = reverse('entrypoint:entrypoint')

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.app = Client()
        self.auth_headers = {
            'HTTP_X_CS_ACCOUNT_TYPE': 'ADMIN',
            'HTTP_X_CS_USER_ID': 190,
        }

        class Config:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        self.mocker.patch(
            'entrypoint.commands.Config'
        ).return_value = Config(version='2.5.6', name='test')

    def test_get(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c = eg.command()
        render = Mock(return_value={'UPDATE_HELLO': c})
        renderer.return_value = Mock(render=render)

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        del c['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'UPDATE_HELLO': CommandSerializer(c).data,
            },
        }

    def test_get__default_query_params_values(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c = eg.command()
        render = Mock(return_value={'UPDATE_HELLO': c})
        renderer.return_value = Mock(render=render)

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        commands = response.json()['commands']

        # -- by default schemas are not hidden
        assert commands['UPDATE_HELLO'].get('schemas') is not None

        # -- but examples are
        assert commands['UPDATE_HELLO'].get('examples') is None

    def test_get__filter_by_commands_query(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c0, c1, c2 = eg.command(), eg.command(), eg.command()
        render = Mock(return_value={
            'UPDATE_HELLO': c0,
            'READ_PAYMENTS': c1,
            'FIND_TOOL': c2,
        })
        renderer.return_value = Mock(render=render)

        # -- filter two commands
        response = self.app.get(
            self.uri,
            data={
                'commands': ['UPDATE_HELLO', 'FIND_TOOL']
            },
            **self.auth_headers)

        assert response.status_code == 200
        del c0['examples']
        del c2['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'UPDATE_HELLO': CommandSerializer(c0).data,
                'FIND_TOOL': CommandSerializer(c2).data,
            },
        }

        # -- filter single command - triangulation
        response = self.app.get(
            self.uri,
            data={
                'commands': ['READ_PAYMENTS']
            },
            **self.auth_headers)

        assert response.status_code == 200
        del c1['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'READ_PAYMENTS': CommandSerializer(c1).data,
            },
        }

    def test_get__with_schemas__false(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c = eg.command()
        render = Mock(return_value={'UPDATE_HELLO': c})
        renderer.return_value = Mock(render=render)

        response = self.app.get(
            self.uri,
            data={'with_schemas': False},
            **self.auth_headers)

        assert response.status_code == 200
        commands = response.json()['commands']
        assert commands['UPDATE_HELLO'].get('schemas') is None

    def test_get__with_examples__true(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c = eg.command()
        render = Mock(return_value={'UPDATE_HELLO': c})
        renderer.return_value = Mock(render=render)

        response = self.app.get(
            self.uri,
            data={'with_examples': True},
            **self.auth_headers)

        assert response.status_code == 200
        commands = response.json()['commands']
        assert commands['UPDATE_HELLO'].get('examples') is not None
        assert renderer.call_args_list == [call()]

    def test_get__filter_by_is_private(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c0 = eg.command(is_private=True)
        c1 = eg.command(is_private=False)
        c2 = eg.command(is_private=True)
        render = Mock(return_value={
            'UPDATE_HELLO': deepcopy(c0),
            'CREATE_HELLO': deepcopy(c1),
            'DELETE_HELLO': deepcopy(c2),
        })
        renderer.return_value = Mock(render=render)

        # -- show only private commands
        response = self.app.get(
            self.uri,
            data={'is_private': True},
            **self.auth_headers)

        assert response.status_code == 200
        del c0['examples']
        del c2['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'UPDATE_HELLO': CommandSerializer(c0).data,
                'DELETE_HELLO': CommandSerializer(c2).data,
            },
        }

        # -- show only public commands
        response = self.app.get(
            self.uri,
            data={'is_private': False},
            **self.auth_headers)

        assert response.status_code == 200
        del c1['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'CREATE_HELLO': CommandSerializer(c1).data,
            },
        }

    def test_get__filter_by_domain_id(self):

        renderer = self.mocker.patch('entrypoint.commands.CommandsRenderer')
        c0 = eg.command(domain_id='cards')
        c1 = eg.command(domain_id='paths')
        c2 = eg.command(domain_id='paths')
        render = Mock(return_value={
            'UPDATE_HELLO': deepcopy(c0),
            'CREATE_HELLO': deepcopy(c1),
            'DELETE_HELLO': deepcopy(c2),
        })
        renderer.return_value = Mock(render=render)

        # -- show CARDS domain commands
        response = self.app.get(
            self.uri,
            data={'domain_id': 'cards'},
            **self.auth_headers)

        assert response.status_code == 200
        del c0['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'UPDATE_HELLO': CommandSerializer(c0).data,
            },
        }

        # -- show PATHS domain commands
        response = self.app.get(
            self.uri,
            data={'domain_id': 'PATHS'},
            **self.auth_headers)

        assert response.status_code == 200
        del c1['examples']
        del c2['examples']
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'name': 'test',
            'version': '2.5.6',
            'commands': {
                'CREATE_HELLO': CommandSerializer(c1).data,
                'DELETE_HELLO': CommandSerializer(c2).data,
            },
        }

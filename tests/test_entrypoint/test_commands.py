
from unittest.mock import call
from copy import deepcopy
import json

from django.test import TestCase
from django.urls import reverse
import pytest

from lily.base.test import Client
from entrypoint.commands import (
    EntryPointCommands,
    CommandSerializer,
)
from tests.factory import EntityFactory


ef = EntityFactory()


class MockConfig:

    def __init__(self, **kwargs):
        self.version = '2.5.6'
        self.name = 'test'

    @classmethod
    def get_lily_path(cls):
        return cls._lily_path


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

        self.lily_dir = self.tmpdir.mkdir('.lily')
        self.commands_dir = self.lily_dir.mkdir('commands')

        MockConfig._lily_path = str(self.lily_dir)
        self.mocker.patch(
            'entrypoint.commands.Config', MockConfig)

    def test_get(self):

        c = ef.command()
        self.mocker.patch.object(
            EntryPointCommands,
            'get_commands'
        ).return_value = {
            '@enums': [],
            'UPDATE_HELLO': CommandSerializer(deepcopy(c)).data,
        }

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
            'commands': {
                'UPDATE_HELLO': CommandSerializer(c).data,
            },
        }

    def test_get__with_versions(self):

        c = ef.command()
        self.mocker.patch.object(
            EntryPointCommands,
            'get_commands'
        ).return_value = {
            '@enums': [],
            'UPDATE_HELLO': CommandSerializer(deepcopy(c)).data,
        }
        self.commands_dir.join('2.5.6.json').write('..')
        self.commands_dir.join('2.14.5.json').write('..')
        self.commands_dir.join('2.120.0.json').write('..')
        self.commands_dir.join('1.0.0.json').write('..')

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': ['2.120.0', '2.14.5', '2.5.6', '1.0.0'],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
            'commands': {
                'UPDATE_HELLO': CommandSerializer(c).data,
            },
        }

    def test_get__filter_by_commands_query(self):

        c0, c1, c2 = ef.command(), ef.command(), ef.command()
        self.mocker.patch.object(
            EntryPointCommands,
            'get_commands'
        ).side_effect = [
            {
                '@enums': [],
                'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
                'READ_PAYMENTS': CommandSerializer(deepcopy(c1)).data,
                'FIND_TOOL': CommandSerializer(deepcopy(c2)).data,
            },
            {
                '@enums': [],
                'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
                'READ_PAYMENTS': CommandSerializer(deepcopy(c1)).data,
                'FIND_TOOL': CommandSerializer(deepcopy(c2)).data,
            },
        ]

        # -- filter two commands
        response = self.app.get(
            self.uri,
            data={
                'commands': ['UPDATE_HELLO', 'FIND_TOOL']
            },
            **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
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
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
            'commands': {
                'READ_PAYMENTS': CommandSerializer(c1).data,
            },
        }

    def test_get__filter_by_is_private(self):

        c0 = ef.command(is_private=True)
        c1 = ef.command(is_private=False)
        c2 = ef.command(is_private=True)
        self.mocker.patch.object(
            EntryPointCommands,
            'get_commands'
        ).side_effect = [
            {
                '@enums': [],
                'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
                'CREATE_HELLO': CommandSerializer(deepcopy(c1)).data,
                'DELETE_HELLO': CommandSerializer(deepcopy(c2)).data,
            },
            {
                '@enums': [],
                'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
                'CREATE_HELLO': CommandSerializer(deepcopy(c1)).data,
                'DELETE_HELLO': CommandSerializer(deepcopy(c2)).data,
            },
        ]

        # -- show only private commands
        response = self.app.get(
            self.uri,
            data={'is_private': True},
            **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
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
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
            'commands': {
                'CREATE_HELLO': CommandSerializer(c1).data,
            },
        }

    def test_get__filter_by_domain_id(self):

        c0 = ef.command(domain_id='cards')
        c1 = ef.command(domain_id='paths')
        c2 = ef.command(domain_id='paths')
        self.mocker.patch.object(
            EntryPointCommands,
            'get_commands'
        ).side_effect = [
            {
                '@enums': [{'A': 'C'}],
                'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
                'CREATE_HELLO': CommandSerializer(deepcopy(c1)).data,
                'DELETE_HELLO': CommandSerializer(deepcopy(c2)).data,
            },
            {
                '@enums': [{'A': 'X'}],
                'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
                'CREATE_HELLO': CommandSerializer(deepcopy(c1)).data,
                'DELETE_HELLO': CommandSerializer(deepcopy(c2)).data,
            },
        ]

        # -- show CARDS domain commands
        response = self.app.get(
            self.uri,
            data={'domain_id': 'cards'},
            **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [{'A': 'C'}],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
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
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            '@enums': [{'A': 'X'}],
            'name': 'test',
            'version_info': {
                '@type': 'version_info',
                'available': [],
                'deployed': '2.5.6',
                'displayed': '2.5.6',
            },
            'commands': {
                'CREATE_HELLO': CommandSerializer(c1).data,
                'DELETE_HELLO': CommandSerializer(c2).data,
            },
        }

    def test_get__version(self):

        c = ef.command()
        get_commands = self.mocker.patch.object(
            EntryPointCommands, 'get_commands')
        get_commands.return_value = {
            '@enums': [],
            'UPDATE_HELLO': CommandSerializer(deepcopy(c)).data,
        }

        response = self.app.get(
            self.uri,
            data={'version': '2.1.3'},
            **self.auth_headers)

        assert response.status_code == 200
        version_info = response.json()['version_info']
        assert version_info == {
            '@type': 'version_info',
            'available': [],
            'deployed': '2.5.6',
            'displayed': '2.1.3',
        }
        assert get_commands.call_args_list == [call('2.1.3')]

    #
    # GET_COMMANDS
    #
    def test_get_commands(self):

        c0 = ef.command(domain_id='cards')
        c1 = ef.command(domain_id='paths')

        commands = {
            'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
            'CREATE_HELLO': CommandSerializer(deepcopy(c1)).data,
        }
        self.commands_dir.join('2.5.6.json').write(json.dumps(commands))

        assert EntryPointCommands().get_commands() == commands

    def test_get_commands__version(self):

        c0 = ef.command(domain_id='cards')
        c1 = ef.command(domain_id='paths')

        commands0 = {  # noqa
            'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
            'CREATE_HELLO': CommandSerializer(deepcopy(c1)).data,
        }
        self.commands_dir.join('2.5.6.json').write(json.dumps(commands0))
        commands1 = {
            'UPDATE_HELLO': CommandSerializer(deepcopy(c0)).data,
        }
        self.commands_dir.join('2.0.0.json').write(json.dumps(commands1))

        assert EntryPointCommands().get_commands('2.0.0') == commands1

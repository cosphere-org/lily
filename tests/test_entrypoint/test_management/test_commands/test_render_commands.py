
import json

from click.testing import CliRunner
from django.test import TestCase
import pytest

from lily.entrypoint.management.commands.render_commands import command
from lily.entrypoint.renderer import CommandsRenderer
from lily.entrypoint.serializers import CommandSerializer
from tests.factory import EntityFactory


ef = EntityFactory()


class RenderCommandsTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker

        self.lily_dir = tmpdir.mkdir('.lily')

    def setUp(self):
        self.runner = CliRunner()

    def test_command__no_next_version__makes_the_right_calls(self):

        class ConfigMock:

            @classmethod
            def get_lily_path(cls):
                return str(self.lily_dir)

            @property
            def version(self):
                return '8.9.1'

            @property
            def next_version(self):
                return None

        self.mocker.patch(
            'lily.entrypoint.management.commands.render_commands.Config',
            ConfigMock)

        c0 = ef.command(domain_id='clients')
        c1 = ef.command(domain_id='products')

        self.mocker.patch.object(
            CommandsRenderer,
            'render'
        ).return_value = {
            '@enums': [{'enum_name': 'C'}],
            'BULK_READ_CLIENTS': c0,
            'DELETE_PRODUCT': c1,
        }

        result = self.runner.invoke(command)

        assert result.exit_code == 0
        commands_json = self.lily_dir.join('commands').join('8.9.1.json')
        assert (
            result.output.strip() ==
            f'Commands rendered for to file {str(commands_json)}')
        assert json.loads(commands_json.read()) == {
            '@enums': [{'enum_name': 'C'}],
            'BULK_READ_CLIENTS': CommandSerializer(c0).data,
            'DELETE_PRODUCT': CommandSerializer(c1).data,
        }

    def test_command__next_version__makes_the_right_calls(self):

        class ConfigMock:

            @classmethod
            def get_lily_path(cls):
                return str(self.lily_dir)

            @property
            def version(self):
                return '8.9.1'

            @property
            def next_version(self):
                return '8.9.2'

        self.mocker.patch(
            'lily.entrypoint.management.commands.render_commands.Config',
            ConfigMock)

        c0 = ef.command(domain_id='clients')
        c1 = ef.command(domain_id='products')

        self.mocker.patch.object(
            CommandsRenderer,
            'render'
        ).return_value = {
            '@enums': [],
            'BULK_READ_CLIENTS': c0,
            'DELETE_PRODUCT': c1,
        }

        result = self.runner.invoke(command)

        assert result.exit_code == 0
        commands_json = self.lily_dir.join('commands').join('8.9.2.json')
        assert (
            result.output.strip() ==
            f'Commands rendered for to file {str(commands_json)}')
        assert json.loads(commands_json.read()) == {
            '@enums': [],
            'BULK_READ_CLIENTS': CommandSerializer(c0).data,
            'DELETE_PRODUCT': CommandSerializer(c1).data,
        }

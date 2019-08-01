
from unittest.mock import call
import json

from django.core import management
from django.test import TestCase
from click.testing import CliRunner
import pytest

from migrator.management.commands.apply_migration_plan_for_version import (
    command,
)


class ApplyMigrationPlanForVersionCommandTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

        class MockConfig:

            @classmethod
            def get_lily_path(cls):
                return str(self.tmpdir)

        self.mocker.patch(
            'migrator.management.commands.apply_migration_plan_for_version'
            '.Config',
            MockConfig)

    def test_apply_migrations(self):

        call_command = self.mocker.patch.object(management, 'call_command')

        self.tmpdir.mkdir('migrations').join('6.7.1.json').write(json.dumps({
            'plan': [
                ('auth', '0001_a'),
                ('media', '0002_b'),
            ],
        }))

        result = self.runner.invoke(command, ['6.7.1'])

        assert result.exit_code == 0
        assert result.output.strip() == (
            'Migrations plan for version 6.7.1 applied.')
        assert call_command.call_args_list == [
            call('migrate', 'auth', '0001_a'),
            call('migrate', 'media', '0002_b'),
        ]


import os
from unittest import TestCase
import json

from click.testing import CliRunner
import pytest

from lily.base.management.commands.clear_examples import command


class ClearExamplesCommandTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

    #
    # CLEAR_EXAMPLES
    #
    def test_clear_examples__file_exists(self):

        self.mocker.patch.object(os, 'getcwd').return_value = str(self.tmpdir)
        lily_dir = self.tmpdir.mkdir('.lily')
        lily_dir.join('examples.json').write(json.dumps({'some': 'examples'}))

        result = self.runner.invoke(command)

        assert result.exit_code == 0
        assert result.output.strip() == "'examples.json' was removed"
        assert lily_dir.listdir() == []

    def test_clear_examples__file_does_not_exist(self):

        self.mocker.patch.object(os, 'getcwd').return_value = str(self.tmpdir)
        lily_dir = self.tmpdir.mkdir('.lily')

        result = self.runner.invoke(command)

        assert result.exit_code == 0
        assert result.output.strip() == "'examples.json' was removed"
        assert lily_dir.listdir() == []

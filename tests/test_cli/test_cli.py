
import os
from unittest import TestCase
from unittest.mock import call
import textwrap

from click.testing import CliRunner
import pytest

from lily.cli.cli import cli
from lily.cli.copier import Copier
from tests import remove_white_chars


class CliTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

    #
    # INIT
    #
    def test_init(self):

        copy = self.mocker.patch.object(Copier, 'copy')

        result = self.runner.invoke(cli, ['init', 'src_dir'])
        assert result.exit_code == 0
        assert result.output.strip() == textwrap.dedent('''
            [INFO]

            Please insert the following line at the top of your Makefile:

            include .lily/lily.makefile
        ''').strip()
        assert copy.call_args_list == [call('src_dir')]

    def test_init__config_does_not_exist(self):

        current_cwd = os.getcwd()
        os.chdir(str(self.tmpdir))

        copy = self.mocker.patch.object(Copier, 'copy')

        result = self.runner.invoke(cli, ['init', 'src_dir'])
        assert result.exit_code == 1
        assert remove_white_chars(result.output) == remove_white_chars('''
            Error:
            Please install `lily_assistant` and run
            `lily_assistant init <src_dir>` before running
            `lily init <src_dir>`
        ''')
        assert copy.call_count == 0
        os.chdir(current_cwd)


from unittest import TestCase
from unittest.mock import call
import textwrap

from click.testing import CliRunner
import pytest

from lily.cli.cli import cli
from lily.cli.copier import Copier


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

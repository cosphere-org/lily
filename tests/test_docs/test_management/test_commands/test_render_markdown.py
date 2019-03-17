
from click.testing import CliRunner
from django.test import TestCase
import pytest

from lily_assistant.config import Config

from lily.docs.management.commands.render_markdown import command
from lily.docs.renderers.markdown.renderer import MarkdownRenderer


class RenderMarkdownTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

    def test_command(self):

        lily_dir = self.tmpdir.mkdir('.lily')
        self.mocker.patch.object(
            Config, 'get_lily_path').return_value = str(lily_dir)

        self.mocker.patch.object(
            MarkdownRenderer, 'render').return_value = '# API'

        result = self.runner.invoke(command, [])

        assert result.exit_code == 0
        assert result.output.strip() == (
            'Successfully rendered Markdown Specification for all '
            'registered Commands')
        assert lily_dir.join('API.md').read() == '# API'

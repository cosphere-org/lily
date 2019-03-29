
from unittest.mock import call

from django.test import TestCase
from click.testing import CliRunner
import pytest

from lily.base.utils import normalize_indentation
from lily.docs.management.commands.render_angular import command
from lily.docs.renderers.angular.renderer import AngularClientRenderer


class RenderAngularTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        self.runner = CliRunner()

    def test_command__makes_the_right_calls(self):

        renderer = self.mocker.patch(  # noqa
            'lily.docs.management.commands.render_angular'
            '.AngularClientRenderer')

        result = self.runner.invoke(
            command, ['origin', 'super', '--only_build'])

        assert result.exit_code == 0
        assert normalize_indentation(
            result.output, 0
        ) == normalize_indentation(
            '''
                - Successfully rendered and built Angular Client [NO PUSHING TO REMOTE]
            ''', 0)  # noqa
        assert renderer.call_args_list == [call('origin', 'super')]
        assert renderer.return_value.render.call_args_list == [
            call(exclude_domains=(), include_domains=(), only_build=True),
        ]

    def test_command__default_values(self):

        render = self.mocker.patch.object(AngularClientRenderer, 'render')
        render.return_value = '1.0.19'

        result = self.runner.invoke(command, ['origin', 'super'])

        assert result.exit_code == 0
        assert normalize_indentation(
            result.output, 0
        ) == normalize_indentation(
            '''
                - Successfully rendered and pushed Angular Client version: 1.0.19
            ''', 0)  # noqa
        assert render.call_args_list == [
            call(exclude_domains=(), include_domains=(), only_build=None),
        ]

    def test_command__include_and_exclude_domains(self):

        render = self.mocker.patch.object(AngularClientRenderer, 'render')
        render.return_value = '1.0.19'

        result = self.runner.invoke(
            command,
            [
                'origin',
                'super',
                '--only_build',
                '--include_domain', 'CARDS',
                '--exclude_domain', 'PATHS',
                '--exclude_domain', 'GOSSIP',
            ])

        assert result.exit_code == 0
        assert render.call_args_list == [
            call(
                exclude_domains=('PATHS', 'GOSSIP'),
                include_domains=('CARDS',),
                only_build=True,
            ),
        ]

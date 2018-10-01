# -*- coding: utf-8 -*-

from django.test import TestCase
from click.testing import CliRunner
import pytest
from mock import call

from lily.base.utils import normalize_indentation
from lily.repo.management.commands.upgrade_version import command
from lily.repo.version import VersionRenderer
from lily.repo.changelog import ChangelogRenderer
from lily.repo.repo import Repo


class ConfigMock:

    def __init__(self, version, last_commit_hash, path):
        self._version = version
        self._last_commit_hash = last_commit_hash
        self._path = path

    @property
    def path(self):
        return self._path

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def last_commit_hash(self):
        return self._last_commit_hash

    @last_commit_hash.setter
    def last_commit_hash(self, value):
        self._last_commit_hash = value


class UpgradeVersionTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        self.runner = CliRunner()

    def test_command__makes_the_right_calls(self):

        self.mocker.patch.object(Repo, 'current_commit_hash', '222222')
        repo_add = self.mocker.patch.object(Repo, 'add')
        repo_commit = self.mocker.patch.object(Repo, 'commit')
        repo_push = self.mocker.patch.object(Repo, 'push')
        repo_tag = self.mocker.patch.object(Repo, 'tag')
        render_next_version = self.mocker.patch.object(
            VersionRenderer, 'render_next_version')
        render_next_version.return_value = '1.2.13'

        changelog_render = self.mocker.patch.object(
            ChangelogRenderer, 'render')

        config = ConfigMock(
            version='1.2.12',
            last_commit_hash='111111',
            path='/hello/world')
        self.mocker.patch(
            'lily.repo.management.commands.upgrade_version.Config',
        ).return_value = config

        result = self.runner.invoke(
            command, [VersionRenderer.VERSION_UPGRADE.MAJOR])

        assert result.exit_code == 0
        assert normalize_indentation(
            result.output, 0
        ) == normalize_indentation(
            '''
                - Version upgraded to: 1.2.13
                - branch tagged
                - CHANGELOG rendered
            ''', 0)

        assert config.version == '1.2.13'
        assert config.last_commit_hash == '222222'

        assert render_next_version.call_args_list == [call('1.2.12', 'MAJOR')]
        assert changelog_render.call_args_list == [call()]

        assert repo_add.call_args_list == [call('/hello/world')]
        assert repo_tag.call_args_list == [call('1.2.13')]
        assert repo_commit.call_args_list == [call('VERSION: 1.2.13')]
        assert repo_push.call_args_list == [call()]

    def test_command__invalid_upgrade_type(self):

        result = self.runner.invoke(command, ['NOT_MAJOR'])

        assert result.exit_code == 2
        assert 'Invalid value for "upgrade_type"' in result.output

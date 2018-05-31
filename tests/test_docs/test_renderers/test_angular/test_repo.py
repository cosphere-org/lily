# -*- coding: utf-8 -*-

from django.test import TestCase
import pytest
from mock import call

from lily.docs.renderers.angular.repo import AngularRepo
from lily.repo.version import VersionRenderer


class AngularRepoTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    #
    # GIT
    #
    def test_commit(self):
        git = self.mocker.patch.object(AngularRepo, 'git')
        r = AngularRepo()

        r.commit('0.9.11')

        assert git.call_args_list == [call('commit -m "ADDED version 0.9.11"')]

    #
    # NPM
    #
    def test_build(self):
        npm = self.mocker.patch.object(AngularRepo, 'npm')
        r = AngularRepo()

        r.build()

        assert npm.call_args_list == [call('run build')]

    def test_install(self):
        npm = self.mocker.patch.object(AngularRepo, 'npm')
        r = AngularRepo()

        r.install()

        assert npm.call_args_list == [call('install')]

    def test_npm(self):
        execute = self.mocker.patch.object(AngularRepo, 'execute')
        r = AngularRepo()

        r.npm('whatever')

        assert execute.call_args_list == [call('npm whatever')]

    #
    # UPGRADE VERSION
    #
    def test_upgrade_version(self):

        path = self.tmpdir.mkdir('repo')
        package = path.join('package.json')
        package.write('"version": "{}"'.format('0.1.18'))
        AngularRepo.base_path = str(path)
        r = AngularRepo()

        assert r.upgrade_version(
            VersionRenderer.VERSION_UPGRADE.MINOR) == '0.1.19'
        with open('package.json') as f:
            assert f.read() == '"version": "0.1.19"'

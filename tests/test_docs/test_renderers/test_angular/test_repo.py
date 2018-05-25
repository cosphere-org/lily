# -*- coding: utf-8 -*-

import subprocess
import os

from django.test import TestCase
import pytest
from mock import call

from lily.docs.renderers.angular.repo import Repo


class RepoTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    #
    # GIT
    #
    def test_push(self):
        git = self.mocker.patch.object(Repo, 'git')
        r = Repo()

        r.push()

        assert git.call_args_list == [call('push origin master')]

    def test_pull(self):
        git = self.mocker.patch.object(Repo, 'git')
        r = Repo()

        r.pull()

        assert git.call_args_list == [call('pull origin master')]

    def test_add_all(self):
        git = self.mocker.patch.object(Repo, 'git')
        r = Repo()

        r.add_all()

        assert git.call_args_list == [call('add .'), call('add -u .')]

    def test_commit(self):
        git = self.mocker.patch.object(Repo, 'git')
        r = Repo()

        r.commit('0.9.11')

        assert git.call_args_list == [call('commit -m "ADDED version 0.9.11"')]

    def test_git(self):
        execute = self.mocker.patch.object(Repo, 'execute')
        r = Repo()

        r.git('whatever')

        assert execute.call_args_list == [call('git whatever')]

    #
    # NPM
    #
    def test_build(self):
        npm = self.mocker.patch.object(Repo, 'npm')
        r = Repo()

        r.build()

        assert npm.call_args_list == [call('run build')]

    def test_install(self):
        npm = self.mocker.patch.object(Repo, 'npm')
        r = Repo()

        r.install()

        assert npm.call_args_list == [call('install')]

    def test_npm(self):
        execute = self.mocker.patch.object(Repo, 'execute')
        r = Repo()

        r.npm('whatever')

        assert execute.call_args_list == [call('npm whatever')]

    #
    # UTILS
    #
    def test_execute(self):
        check_output = self.mocker.patch.object(subprocess, 'check_output')
        check_output.return_value = b'hello'
        r = Repo()

        r.execute('hello')

        assert check_output.call_args_list == [
            call('hello', shell=True, stderr=subprocess.STDOUT)]

    #
    # DIR / FILES
    #
    def test_clear_dir(self):
        base_dir = self.tmpdir.mkdir('base')
        hi_dir = base_dir.mkdir('hi')
        hi_dir.join('hello.txt').write('hi')
        hi_dir.join('bye.md').write('bye')
        Repo.base_path = str(base_dir)

        r = Repo()

        assert sorted(os.listdir(str(hi_dir))) == ['bye.md', 'hello.txt']

        r.clear_dir('hi')

        assert os.listdir(str(hi_dir)) == []

    def test_create_dir(self):
        hi_dir = self.tmpdir.mkdir('hi')
        Repo.base_path = str(hi_dir)

        r = Repo()

        r.create_dir('hello')

        assert os.path.exists(os.path.join(str(hi_dir), 'hello')) is True

    def test_create_dir__twice(self):
        hi_dir = self.tmpdir.mkdir('hi')
        Repo.base_path = str(hi_dir)

        r = Repo()

        r.create_dir('hello')
        r.create_dir('hello')


@pytest.mark.parametrize(
    'current_version, upgrade_type, expected_version',
    [
        # -- patch version upgrade
        ('0.1.11', Repo.VERSION_UPGRADE.PATCH, '0.1.12'),

        # -- patch version upgrade - triangulation
        ('6.14.23', Repo.VERSION_UPGRADE.PATCH, '6.14.24'),

        # -- minor version upgrade
        ('0.1.11', Repo.VERSION_UPGRADE.MINOR, '0.2.0'),

        # -- minor version upgrade - triangulation
        ('6.14.23', Repo.VERSION_UPGRADE.MINOR, '6.15.0'),

        # -- major version upgrade
        ('0.1.11', Repo.VERSION_UPGRADE.MAJOR, '1.0.0'),

        # -- major version upgrade - triangulation
        ('6.14.23', Repo.VERSION_UPGRADE.MAJOR, '7.0.0'),
    ])
def test_repo_upgrade_version(
        current_version, upgrade_type, expected_version, tmpdir):

    path = tmpdir.mkdir('repo')
    package = path.join('package.json')
    package.write('"version": "{}"'.format(current_version))
    Repo.base_path = str(path)
    r = Repo()

    assert r.upgrade_version(upgrade_type) == expected_version
    with open('package.json') as f:
        assert f.read() == '"version": "{}"'.format(expected_version)

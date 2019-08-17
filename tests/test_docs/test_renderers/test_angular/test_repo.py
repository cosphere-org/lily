
import os
import tempfile
import textwrap
from unittest.mock import call

from django.test import TestCase, override_settings
import pytest
from lily_assistant.repo.repo import Repo

from lily.docs.renderers.angular.repo import (
    AngularHTTPRepo,
    AngularRepo,
    TemplateRepo,
    PathRule,
)


class AngularHTTPRepoTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    #
    # LINK
    #
    def test_link(self):
        npm = self.mocker.patch.object(AngularHTTPRepo, 'npm')
        r = AngularHTTPRepo()

        r.link()

        assert npm.call_args_list == [call('link')]


class AngularRepoTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.current_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.current_cwd)

    #
    # GIT
    #
    def test_commit(self):
        git = self.mocker.patch.object(AngularRepo, 'git')
        r = AngularRepo('origin')

        r.commit('0.9.11')

        assert git.call_args_list == [call('commit -m "ADDED version 0.9.11"')]

    #
    # NPM
    #
    def test_build(self):
        npm = self.mocker.patch.object(AngularRepo, 'npm')
        r = AngularRepo('origin')

        r.build()

        assert npm.call_args_list == [call('run build')]

    def test_install(self):
        npm = self.mocker.patch.object(AngularRepo, 'npm')
        r = AngularRepo('origin')

        r.install()

        assert npm.call_args_list == [call('install')]

    def test_npm(self):
        execute = self.mocker.patch.object(AngularRepo, 'execute')
        r = AngularRepo('origin')

        r.npm('whatever')

        assert execute.call_args_list == [call('npm whatever')]

    #
    # UPGRADE VERSION
    #
    def test_upgrade_version(self):

        class MockConfig:

            @property
            def version(self):
                return '0.9.1'

        temp_dir = self.tmpdir.mkdir('repo')
        package = temp_dir.join('package.json')
        package.write('"version": "{}"'.format('0.1.18'))

        self.mocker.patch.object(
            tempfile, 'mkdtemp').return_value = str(temp_dir)

        r = AngularRepo('origin')
        r.cd_to_repo()

        assert r.upgrade_version(MockConfig()) == '0.9.1-API-0.1.18-CLIENT'
        with open('package.json') as f:
            assert f.read() == '"version": "0.9.1-API-0.1.18-CLIENT"'


class PathRuleTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, tmpdir):
        self.tmpdir = tmpdir

    #
    # MATCHES
    #
    def test_matches__file(self):

        rule = PathRule(r'.*\.json$')

        assert rule.matches('/hi/there.json') is True
        assert rule.matches('/hi/there.json123') is False
        assert rule.matches('woeldOfjson') is False
        assert rule.matches('this.JSON') is True

    def test_matches__directory(self):

        base_dir = self.tmpdir
        base_dir.mkdir('modules')

        rule = PathRule(r'.*modules', True)

        assert rule.matches(str(base_dir.join('modules'))) is True
        assert rule.matches(str(base_dir.join('modules/here'))) is True
        assert rule.matches(str(base_dir.join('modules123'))) is False
        assert rule.matches(str(base_dir.join('modles'))) is False

    def test_matches__matched_but_not_directory(self):

        file = self.tmpdir.mkdir('hello').join('modules').write('hi')

        rule = PathRule(r'.*modules')

        assert rule.matches(str(file)) is False


class TemplateRepoTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    #
    # CLONE
    #
    @override_settings(LILY_ANGULAR_CLIENT_ORIGIN='some_origin')
    def test_clone__makes_the_right_calls(self):

        clone = self.mocker.patch.object(Repo, 'clone')
        temp_dir = self.tmpdir.mkdir('123')
        self.mocker.patch.object(
            tempfile, 'mkdtemp').return_value = str(temp_dir)
        repo = TemplateRepo()

        repo.clone()

        assert clone.call_args_list == [call(str(temp_dir))]

    #
    # COPY_TO
    #
    def test_copy_to__ignores_and_keeps(self):

        source_dir = self.tmpdir.mkdir('source')
        d_0 = source_dir.mkdir('d_0')

        f_0_0 = d_0.join('f_0_0.md')
        f_0_0.write('f_0_0')

        f_0_1 = d_0.join('f_0_1.js')  # noqa - will be ignored
        f_0_1.write('f_0_1')

        d_0_0 = d_0.mkdir('d_0_0')

        f_0_0_0 = d_0_0.join('f_0_0_0.json')
        f_0_0_0.write('f_0_0_0')

        f_0_0_1 = d_0_0.join('f_0_0_1.ts')
        f_0_0_1.write('f_0_0_1')

        d_1 = source_dir.mkdir('d_1')

        f_1_0 = d_1.join('f_1_0.ico')
        f_1_0.write('f_1_0')

        self.mocker.patch.object(
            tempfile, 'mkdtemp').return_value = str(source_dir)

        destination_dir = self.tmpdir.mkdir('destination')
        repo = TemplateRepo()

        repo.copy_to(str(destination_dir), 'extra')

        assert set(os.listdir(destination_dir)) == set(['d_0', 'd_1'])
        assert (
            set(os.listdir(destination_dir.join('d_0'))) ==
            set(['f_0_0.md', 'd_0_0']))
        assert (
            set(os.listdir(destination_dir.join('d_0/d_0_0'))) ==
            set(['f_0_0_0.json', 'f_0_0_1.ts']))
        assert (
            set(os.listdir(destination_dir.join('d_1'))) ==
            set(['f_1_0.ico']))

    def test_copy_to__cleans_up_before_copy(self):

        source_dir = self.tmpdir.mkdir('source')
        d = source_dir.mkdir('d')
        f = d.join('f.md')
        f.write('f')

        destination_dir = self.tmpdir.mkdir('destination')

        # -- should be kept
        git_dir = destination_dir.mkdir('.git')
        git_dir.join('hook').write('hook it')

        # -- should be removed
        dd = destination_dir.mkdir('dd')
        dd.join('hi.txt').write('hello')
        destination_dir.join('root.js').write('root it')

        self.mocker.patch.object(
            tempfile, 'mkdtemp').return_value = str(source_dir)

        repo = TemplateRepo()

        repo.copy_to(str(destination_dir), 'extra')

        assert set(os.listdir(destination_dir)) == set(['d', '.git'])
        assert os.listdir(destination_dir.join('d')) == ['f.md']
        assert os.listdir(destination_dir.join('.git')) == ['hook']

    #
    # IGNORE
    #
    def test_ignore__ignores(self):

        repo = TemplateRepo()

        self.tmpdir.mkdir('node_modules')
        self.tmpdir.mkdir('node_modules/hello')
        self.tmpdir.mkdir('.git')
        self.tmpdir.mkdir('hi')

        to_ignore = repo.ignore(
            str(self.tmpdir),
            [
                # -- ignore: node_modules and all its children
                'node_modules',
                'node_modules/hello',
                'node_modules/angular.ts',

                # -- ignore: .git and all its children
                '.git',
                '.git/hooks',
                '.git/whatever.json',

                # -- no ignore .ts
                'hello.ts',
                'hi/hello.ts',
            ])

        assert set(to_ignore) == set([
            '.git',
            '.git/hooks',
            '.git/whatever.json',

            'node_modules',
            'node_modules/hello',
            'node_modules/angular.ts',
        ])

    def test_ignore__keeps(self):

        repo = TemplateRepo()

        self.tmpdir.mkdir('x')
        self.tmpdir.mkdir('x/y')

        to_ignore = repo.ignore(
            str(self.tmpdir),
            [
                # -- exceptions
                'a/karma.conf.js',
                'a/browserslist',
                'a/.npmignore',
                'a/.gitkeep',

                # -- ts
                'a/hi.ts',
                'a/b/service.ts',

                # -- html
                'b/app.html',
                'b/c/what.html',

                # -- json
                'hi.json',
                'c/wat.json',

                # -- ico
                'hi.ico',
                'c/wat.ico',

                # -- css
                'hi.css',
                'c/wat.css',

                # -- all other directories
                'x/what.json',
                'x/y/whatever.ts',
            ])

        # -- all to keep
        assert to_ignore == []

    #
    # COPY
    #
    def test_copy(self):

        source = self.tmpdir.join('hello.ts')
        source.write('hello there')

        destination = self.tmpdir.join('copy_hello.ts')

        repo = TemplateRepo()

        repo.copy('super', str(source), str(destination))

        assert destination.read() == 'hello there'

    def test_copy__replaces_prefix(self):

        source = self.tmpdir.join('hello.ts')
        source.write(textwrap.dedent('''
            hello __CLIENT_PREFIX__

            __CLIENT_PREFIX__ is cool.
        '''))

        destination = self.tmpdir.join('copy_hello.ts')

        repo = TemplateRepo()

        repo.copy('super', str(source), str(destination))

        assert destination.read() == textwrap.dedent('''
            hello super

            super is cool.
        ''')

    def test_copy__deals_with_binary_files(self):

        source = self.tmpdir.join('hello.ico')
        source.write(b'\x00\x00\x01\x00\x02\x00\x10\x10\x00\x00', 'wb')

        destination = self.tmpdir.join('copy_hello.ico')

        repo = TemplateRepo()

        repo.copy('super', str(source), str(destination))

        assert destination.read() == '\x00\x00\x01\x00\x02\x00\x10\x10\x00\x00'

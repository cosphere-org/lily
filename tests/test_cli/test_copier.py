
from unittest import TestCase
from unittest.mock import call
import json
import os
import textwrap

import pytest

from lily.cli.copier import Copier


class CopierTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, tmpdir, mocker):
        self.tmpdir = tmpdir
        self.mocker = mocker

    def setUp(self):
        self.cli_dir = self.tmpdir.mkdir('cli_dir')
        self.project_dir = self.tmpdir.mkdir('project')
        self.project_dir.mkdir('.lily').join('config.json').write(json.dumps({
            'version': '0.0.11'
        }))
        os.chdir(str(self.project_dir))

    #
    # COPY
    #
    def test_copy__makes_the_right_calls(self):

        create_empty_config = self.mocker.patch.object(
            Copier, 'create_empty_config')
        copy_makefile = self.mocker.patch.object(Copier, 'copy_makefile')

        Copier().copy('gigly')

        assert create_empty_config.call_args_list == [call('gigly')]
        assert copy_makefile.call_args_list == [call('gigly')]

    #
    # CREATE_EMPTY_CONFIG
    #
    def test_create_empty_config__does_not_exist(self):

        config_json = self.project_dir.join('.lily').join('config.json')

        assert json.loads(config_json.read()) == {
            'version': '0.0.11'
        }

        Copier().create_empty_config('gigly')

        assert json.loads(config_json.read()) == {
            'version': '0.0.11'
        }

    def test_create_empty_config__exists(self):

        config_json = self.project_dir.join('.lily').join('config.json')

        os.remove(str(config_json))

        Copier().create_empty_config('gigly')

        assert json.loads(config_json.read()) == {
            'last_commit_hash': '... THIS WILL BE FILLED AUTOMATICALLY ...',
            'name': '... PUT HERE NAME OF YOUR PROJECT ...',
            'repository': '... PUT HERE URL OF REPOSITORY ...',
            'src_dir': 'gigly',
            'version': '... PUT HERE INITIAL VERSION ...',
        }

    #
    # COPY_MAKEFILE
    #
    def test_copy_makefile__copies_makefile(self):

        makefile = self.cli_dir.join('base.makefile')
        makefile.write(textwrap.dedent('''
            ## GENERATED FOR VERSION: {% VERSION %}

            lint:  ## lint the {% SRC_DIR %} & tests
                source env.sh && \
                flake8 --ignore D100,D101 tests && \
                flake8 --ignore D100,D101 {% SRC_DIR %}
        '''))
        self.mocker.patch.object(Copier, 'base_makefile_path', str(makefile))

        Copier().copy_makefile('gigly')

        result_makefile_content = (
            self.project_dir.join('.lily/lily.makefile').read())
        assert result_makefile_content == textwrap.dedent('''
            ## GENERATED FOR VERSION: 0.0.11

            lint:  ## lint the gigly & tests
                source env.sh && \
                flake8 --ignore D100,D101 tests && \
                flake8 --ignore D100,D101 gigly
        ''')

    def test_copy_makefile__copies_makefile__with_override(self):

        makefile = self.cli_dir.join('base.makefile')
        makefile.write('NEW make it')
        self.mocker.patch.object(Copier, 'base_makefile_path', str(makefile))
        self.project_dir.join(
            '.lily/lily.makefile').write('OLD make it')

        Copier().copy_makefile('gigly')

        assert (
            self.project_dir.join('.lily/lily.makefile').read() ==
            'NEW make it')


import os
from unittest.mock import call, Mock
import importlib
import json

from django.test import TestCase
from click.testing import CliRunner
import pytest

from migrator.management.commands.render_current_migration_plan import (
    Renderer,
    command,
)


def migration_class(dependencies=None):

    return Mock(Migration=Mock(dependencies=dependencies or []))


class RendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()
        self.renderer = Renderer()

        class MockConfig:

            @property
            def src_dir(self):
                return 'src'

        self.mocker.patch(
            'migrator.management.commands.render_current_migration_plan'
            '.Config',
            MockConfig)

        self.prev_dir = os.getcwd()
        srcdir = self.tmpdir.mkdir('src')

        os.chdir(self.tmpdir)

        # -- BUILD BASIC STRUCTURE
        self.auth_dir = srcdir.mkdir('auth').mkdir('migrations')
        self.task_dir = srcdir.mkdir('task').mkdir('migrations')
        self.todo_dir = srcdir.mkdir('todo').mkdir('migrations')

    def tearDown(self):
        os.chdir(self.prev_dir)

    #
    # RENDER
    #
    def test_render__makes_the_right_calls(self):

        get_dependencies = self.mocker.patch.object(
            Renderer, 'get_dependencies')
        get_dependencies.return_value = {
            ('app0', '001_what'): set(['what']),
            ('app1', '006_why'): set(),
        }
        get_most_current_migrations = self.mocker.patch.object(
            Renderer, 'get_most_current_migrations')
        get_migrations_plan = self.mocker.patch.object(
            Renderer, 'get_migrations_plan')

        the_plan = self.renderer.render()

        assert the_plan == {
            'plan': get_migrations_plan.return_value,
            'dependencies': {
                'app0.001_what': ['what'],
                'app1.006_why': [],
            }
        }
        assert get_dependencies.call_args_list == [
            call(get_most_current_migrations.return_value),
        ]
        assert get_migrations_plan.call_args_list == [
            call(get_dependencies.return_value),
        ]

    #
    # GET_MOST_CURRENT_MIGRATIONS
    #
    def test_get_most_current_migrations__no_migrations(self):

        self.renderer.get_most_current_migrations() == []

    def test_get_most_current_migrations__only_current_migrations(self):

        self.auth_dir.join('0001_add_column.py').write(migration_class())
        self.task_dir.join('0001_add_model.py').write(migration_class())

        assert self.renderer.get_most_current_migrations() == [
            (
                'task',
                '0001_add_model',
                'src.task.migrations.0001_add_model',
            ),
            (
                'auth',
                '0001_add_column',
                'src.auth.migrations.0001_add_column',
            ),
        ]

    def test_get_most_current_migrations__not_only_current_migrations(self):

        self.auth_dir.join('0001_add_column.py').write(migration_class())
        self.auth_dir.join('0002_remove_column.py').write(migration_class())
        self.auth_dir.join('0003_rename_column.py').write(migration_class())

        self.task_dir.join('0001_add_model.py').write(migration_class())
        self.task_dir.join('0002_add_column.py').write(migration_class())

        assert self.renderer.get_most_current_migrations() == [
            (
                'task',
                '0002_add_column',
                'src.task.migrations.0002_add_column',
            ),
            (
                'auth',
                '0003_rename_column',
                'src.auth.migrations.0003_rename_column',
            ),
        ]

    #
    # GET_DEPENDENCIES
    #
    def test_get_dependencies__no_dependencies(self):

        self.mocker.patch.object(importlib, 'import_module').side_effect = [
            migration_class(),
            migration_class(),
        ]

        assert self.renderer.get_dependencies([
            ('auth', '0001_add_column', 'auth.migrations.0001_add_column'),
            ('task', '0002_add_column', 'task.migrations.0002_add_column'),
        ]) == {
            ('auth', '0001_add_column'): set(),
            ('task', '0002_add_column'): set(),
        }

    def test_get_dependencies__some_dependencies__between_each_other(self):

        self.mocker.patch.object(importlib, 'import_module').side_effect = [
            migration_class([
                ('task', '0002_add_record'),
                ('todo', '0011_move_record'),
            ]),
            migration_class(),
            migration_class([
                ('task', '0002_add_record'),
            ]),
        ]

        assert self.renderer.get_dependencies([
            ('auth', '0001_add_record', 'auth.migrations.0001_add_record'),
            ('task', '0002_add_record', 'task.migrations.0002_add_record'),
            ('todo', '0011_move_record', 'todo.migrations.0011_move_record'),
        ]) == {
            ('auth', '0001_add_record'): set([
                ('task', '0002_add_record'),
                ('todo', '0011_move_record'),
            ]),
            ('task', '0002_add_record'): set(),
            ('todo', '0011_move_record'): set([
                ('task', '0002_add_record'),
            ]),
        }

    def test_get_dependencies__some_dependencies__some_external(self):

        self.mocker.patch.object(importlib, 'import_module').side_effect = [
            migration_class([
                ('task', '0002_add_row'),
                ('product', '00038_add_model'),
            ]),
            migration_class(),
            migration_class([
                ('task', '0002_add_row'),
            ]),
        ]

        assert self.renderer.get_dependencies([
            ('auth', '0001_add_row', 'auth.migrations.0001_add_row'),
            ('task', '0002_add_row', 'task.migrations.0002_add_row'),
            ('todo', '0011_move_row', 'todo.migrations.0011_move_row'),
        ]) == {
            ('auth', '0001_add_row'): set([
                ('task', '0002_add_row'),
                ('product', '00038_add_model'),
            ]),
            ('task', '0002_add_row'): set(),
            ('todo', '0011_move_row'): set([
                ('task', '0002_add_row'),
            ]),
        }

    #
    # GET_MIGRATIONS_PLAN
    #
    def test_get_migrations_plan__no_migrations(self):

        assert self.renderer.get_migrations_plan({}) == []

    def test_get_migrations_plan__single_migration_with_prev_dependency(self):

        assert self.renderer.get_migrations_plan({
            ('search', '0002_a'): set([
                ('search', '0001_a'),
            ]),
        }) == [
            ('search', '0002_a'),
        ]

    def test_get_migrations_plan__no_dependencies(self):

        assert self.renderer.get_migrations_plan({
            ('auth', '0001_add_column'): set(),
            ('task', '0002_add_column'): set(),
            ('todo', '0011_move_column'): set(),
        }) == [
            ('auth', '0001_add_column'),
            ('task', '0002_add_column'),
            ('todo', '0011_move_column'),
        ]

    def test_get_migrations_plan__some_dependencies(self):

        assert self.renderer.get_migrations_plan({
            ('auth', '0001_c'): set([
                ('task', '0002_c'),
                ('todo', '0011_c'),
                ('joke', '0001_c'),
            ]),
            ('task', '0002_c'): set(),
            ('todo', '0011_c'): set([
                ('task', '0002_c'),
            ]),
        }) == [
            ('task', '0002_c'),
            ('todo', '0011_c'),
            ('auth', '0001_c'),
        ]


class RenderCurrentMigrationPlanCommandTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

        class MockConfig:

            @property
            def version(self):
                return '0.9.1'

            @property
            def next_version(self):
                return None

            @classmethod
            def get_lily_path(cls):
                return str(self.tmpdir)

        self.mocker.patch(
            'migrator.management.commands.render_current_migration_plan'
            '.Config',
            MockConfig)

    def test_migrations_directory_created_with_migration_file(self):

        self.mocker.patch.object(Renderer, 'render').return_value = {
            'some': 'thing',
        }
        result = self.runner.invoke(command)

        assert result.exit_code == 0
        assert result.output.strip() == (
            f'Migrations plan rendered for to file {str(self.tmpdir)}'
            f'/migrations/0.9.1.json')
        assert self.tmpdir.listdir() == [self.tmpdir.join('migrations')]
        assert self.tmpdir.join('migrations').listdir() == [
            self.tmpdir.join('migrations').join('0.9.1.json')
        ]
        assert json.loads(
            self.tmpdir.join('migrations').join('0.9.1.json').read('r')
        ) == {
            'some': 'thing',
        }

    def test_migrations_directory_already_exists(self):

        self.tmpdir.mkdir('migrations').join('0.9.0.json').write('{}')
        self.mocker.patch.object(Renderer, 'render').return_value = {
            'some': 'thing',
        }
        result = self.runner.invoke(command)

        assert result.exit_code == 0
        assert result.output.strip() == (
            f'Migrations plan rendered for to file {str(self.tmpdir)}'
            f'/migrations/0.9.1.json')
        assert self.tmpdir.listdir() == [self.tmpdir.join('migrations')]
        assert self.tmpdir.join('migrations').listdir() == [
            self.tmpdir.join('migrations').join('0.9.0.json'),
            self.tmpdir.join('migrations').join('0.9.1.json'),
        ]
        assert json.loads(
            self.tmpdir.join('migrations').join('0.9.1.json').read('r')
        ) == {
            'some': 'thing',
        }

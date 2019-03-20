
from unittest import TestCase
import json
import os

from click.testing import CliRunner
import pytest

from lily.cli.cli import cli


class CliTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def init_fixtures(self, mocker, tmpdir):
        self.mocker = mocker
        self.tmpdir = tmpdir

    def setUp(self):
        self.runner = CliRunner()

    #
    # ASSERT_QUERY_PARSER_FIELDS_ARE_OPTIONAL
    #
    def test_assert_query_parser_fields_are_optional(self):

        self.mocker.patch.object(os, 'getcwd').return_value = str(self.tmpdir)
        lily_dir = self.tmpdir.mkdir('.lily')
        lily_dir.join('config.json').write(json.dumps({'version': '9.1.4'}))

        commands_dir = lily_dir.mkdir('commands')
        commands_dir.join('9.1.4.json').write(json.dumps({
            'BULK_READ_WHAT': {
                'schemas': {
                    'input_query': {
                        'schema': {
                            'required': [],
                        }
                    }
                }
            },
            'DELETE_IT': {
                'schemas': {
                }
            },
        }))

        result = self.runner.invoke(
            cli,
            ['assert-query-parser-fields-are-optional'])

        assert result.exit_code == 0
        assert result.output.strip() == ''

    def test_assert_query_parser_fields_are_optional__broken_detected(self):

        self.mocker.patch.object(os, 'getcwd').return_value = str(self.tmpdir)
        lily_dir = self.tmpdir.mkdir('.lily')
        lily_dir.join('config.json').write(json.dumps({'version': '9.1.4'}))

        commands_dir = lily_dir.mkdir('commands')
        commands_dir.join('9.1.4.json').write(json.dumps({
            'BULK_READ_WHAT': {
                'schemas': {
                    'input_query': {
                        'schema': {
                            'required': ['ids'],
                        }
                    }
                }
            },
            'DELETE_IT': {
                'schemas': {}
            },
        }))

        result = self.runner.invoke(
            cli,
            ['assert-query-parser-fields-are-optional'])

        assert result.exit_code == 1
        assert result.output.strip() == (
            "Error: ERROR: query parser for 'BULK_READ_WHAT' has some not "
            "optional fields: [ids]")

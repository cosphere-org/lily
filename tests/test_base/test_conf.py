# -*- coding: utf-8 -*-

from django.test import TestCase, override_settings
import yaml
import pytest

from lily.base.conf import Config


class ConfigTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, tmpdir):
        self.tmpdir = tmpdir

    def test_properties(self):

        config_file = self.tmpdir.mkdir('conf').join('config.yaml')
        config_file.write(yaml.dump({
            'name': 'hello',
            'repository': 'bithub',
            'version': '0.1.9',
            'last_commit_hash': '940594',
        }))

        with override_settings(LILY_CONFIG_FILE_PATH=str(config_file)):
            config = Config()

            assert config.name == 'hello'
            assert config.repository == 'bithub'
            assert config.version == '0.1.9'
            assert config.last_commit_hash == '940594'

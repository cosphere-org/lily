# -*- coding: utf-8 -*-

from django.conf import settings
import yaml


# FIXME: test it!!!!!
class Config:

    def __init__(self):
        with open(settings.LILY_CONFIG_FILE_PATH) as f:
            self.config = yaml.load(f.read())

    @property
    def name(self):
        return self.config['name']

    @property
    def repository(self):
        return self.config['repository']

    @property
    def version(self):
        return self.config['version']

    @property
    def last_commit_hash(self):
        return self.config['last_commit_hash']


config = Config()

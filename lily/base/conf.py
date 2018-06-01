# -*- coding: utf-8 -*-

import os

import yaml

from django.conf import settings
from .utils import normalize_indentation


class Config:

    AUTOGENERATED_DOC = (
        'THIS LINE WAS AUTOGENERATED, ALL MANUAL CHANGES CAN BE OVERWRITTEN')

    def __init__(self):
        with open(settings.LILY_CONFIG_FILE_PATH) as f:
            self.config = yaml.load(f.read())

    @property
    def path(self):
        return settings.LILY_CONFIG_FILE_PATH

    @property
    def name(self):
        return self.config['name']

    @property
    def repository(self):
        return self.config['repository']

    #
    # VERSION
    #
    @property
    def version(self):
        return self.config['version'].split('#')[0].strip()

    @version.setter
    def version(self, value):
        self.config['version'] = value
        self.save()

    #
    # LAST_COMMIT_HASH
    #
    @property
    def last_commit_hash(self):
        return self.config['last_commit_hash'].split('#')[0].strip()

    @last_commit_hash.setter
    def last_commit_hash(self, value):
        self.config['last_commit_hash'] = value
        self.save()

    def save(self):
        blocks = []
        with open(settings.LILY_CONFIG_FILE_PATH, 'w') as f:
            blocks.append(normalize_indentation('''
                name: {name}
                version: {version}  # {doc}
                repository: {repository}
                last_commit_hash: {last_commit_hash}  # {doc}
            ''', 0).format(
                name=self.config['name'],
                version=self.config['version'],
                doc=self.AUTOGENERATED_DOC,
                repository=self.config['repository'],
                last_commit_hash=self.config['last_commit_hash'],
            ))

            if self.config.get('author'):
                blocks.append(normalize_indentation('''
                    author: {author}
                ''', 0).format(author=self.config['author']))

            if self.config.get('description'):
                blocks.append(normalize_indentation('''
                    description: {description}
                ''', 0).format(description=self.config['description']))

            f.write('\n{}\n'.format('\n'.join(blocks)))


if os.environ.get('DJANGO_SETTINGS_MODULE'):
    config = Config()

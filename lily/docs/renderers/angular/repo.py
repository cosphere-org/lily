# -*- coding: utf-8 -*-

import os
import re

from lily.repo.repo import Repo
from lily.repo.version import VersionRenderer


class AngularRepo(Repo):

    base_path = os.path.join(
        os.path.dirname(__file__), 'cosphere-client')

    def commit(self, version):
        self.git('commit -m "ADDED version {}"'.format(version))

    #
    # NPM
    #
    def build(self):
        self.npm('run build')

    def install(self):
        self.npm('install')

    def npm(self, command):
        self.execute('npm {}'.format(command))

    #
    # UTILS
    #
    def upgrade_version(
            self, upgrade_type=VersionRenderer.VERSION_UPGRADE.PATCH):

        with open('package.json', 'r') as p:
            conf = p.read()
            version_match = re.search(
                r'\"version\"\:\s\"(?P<version>[\d\.]+)\"', conf, re.M)
            version = version_match.groupdict()['version']
            span = version_match.span()

            next_version = VersionRenderer().render_next_version(version)

        with open('package.json', 'w') as p:
            conf = conf.replace(
                conf[span[0]: span[1]], '"version": "{}"'.format(next_version))
            p.write(conf)

        return next_version

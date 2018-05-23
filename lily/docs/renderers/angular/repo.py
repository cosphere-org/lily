# -*- coding: utf-8 -*-

import os
import shutil
import re
import subprocess


class Repo:

    def __init__(self):
        self.cd_to_repo()

    class VERSION_UPGRADE:  # noqa
        MAJOR = 'MAJOR'

        MINOR = 'MINOR'

        PATCH = 'PATCH'

    base_path = os.path.join(
        os.path.dirname(__file__), 'cosphere-angular-client')

    def cd_to_repo(self):
        os.chdir(self.base_path)

    #
    # GIT
    #
    def push(self):
        self.git('push origin master')

    def pull(self):
        self.git('pull origin master')

    def add_all(self):
        self.git('add -u .')

    def commit(self, version):
        self.git('commit -m "ADDED version {}"'.format(version))

    def git(self, command):
        self.execute('git {}'.format(command))

    #
    # DIR / FILES
    #
    def clear_dir(self, path):

        path = re.sub('^/', '', path)
        path = os.path.join(os.getcwd(), path)

        for filename in os.listdir(path):
            os.remove(os.path.join(path, filename))

    def create_dir(self, path):
        path = re.sub('^/', '', path)
        path = os.path.join(os.getcwd(), path)

        try:
            os.mkdir(path)

        except FileExistsError:
            pass

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
    def execute(self, command):
        captured = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            shell=True)
        print(str(captured, encoding='utf8'))

    def upgrade_version(self, upgrade_type=VERSION_UPGRADE.PATCH):

        with open('package.json', 'r') as p:
            conf = p.read()
            version_match = re.search(
                r'\"version\"\:\s\"(?P<version>[\d\.]+)\"', conf, re.M)
            version = version_match.groupdict()['version']
            span = version_match.span()

            major, minor, patch = version.split('.')
            major, minor, patch = int(major), int(minor), int(patch)

            if upgrade_type == self.VERSION_UPGRADE.MAJOR:
                major += 1

            elif upgrade_type == self.VERSION_UPGRADE.MINOR:
                minor += 1

            elif upgrade_type == self.VERSION_UPGRADE.PATCH:
                patch += 1

            next_version = '{0}.{1}.{2}'.format(major, minor, patch)

        with open('package.json', 'w') as p:
            conf = conf.replace(
                conf[span[0]: span[1]], '"version": "{}"'.format(next_version))
            p.write(conf)

        return next_version

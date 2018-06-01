# -*- coding: utf-8 -*-

import os
import re
import subprocess

import click

from lily.conf import settings


class Repo:

    def __init__(self):
        self.cd_to_repo()

    base_path = settings.LILY_PROJECT_BASE

    def cd_to_repo(self):
        os.chdir(self.base_path)

    #
    # GIT
    #
    def push(self):
        self.git('push origin {}'.format(self.current_branch))

    def stash(self):
        self.git('stash')

    def pull(self):
        self.git('pull origin {}'.format(self.current_branch))

    @property
    def current_branch(self):
        return self.git('rev-parse --abbrev-ref HEAD').strip()

    @property
    def current_commit_hash(self):
        return self.git('rev-parse HEAD').strip()

    def tag(self, version):
        self.git('tag {}'.format(version))
        self.git('push origin --tags')

    def add_all(self):
        self.git('add .')
        self.git('add -u .')

    def add(self, path):
        self.git('add {}'.format(path))

    def commit(self, message):
        self.git('commit -m "{}"'.format(message))

    def git(self, command):
        return self.execute('git {}'.format(command))

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
    # GENERIC
    #
    def execute(self, command):

        click.secho('[EXECUTE] {}'.format(command), fg='blue')
        try:
            captured = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                shell=True)

        except subprocess.CalledProcessError as e:
            click.secho('--- [ERROR] ----------', fg='red')
            print(str(e.output, encoding='utf8'))
            raise

        else:
            click.secho(str(captured, encoding='utf8'), fg='white')

        return str(captured, encoding='utf8')

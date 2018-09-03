# -*- coding: utf-8 -*-

import os
import re
from subprocess import Popen, PIPE, STDOUT

import click

from lily.conf import settings


class Repo:

    base_path = settings.LILY_PROJECT_BASE

    def __init__(self):
        self.cd_to_repo()

    def cd_to_repo(self):
        os.chdir(self.base_path)

    #
    # GIT
    #
    def clone(self, destination):
        self.git(f'clone {self.origin} {destination}')

    def push(self):
        self.git(f'push origin {self.current_branch}')

    def stash(self):
        self.git('stash')

    def pull(self):
        self.git(f'pull origin {self.current_branch}')

    @property
    def current_branch(self):
        return self.git('rev-parse --abbrev-ref HEAD').strip()

    @property
    def current_commit_hash(self):
        return self.git('rev-parse HEAD').strip()

    def tag(self, version):
        self.git(f'tag {version}')
        self.git('push origin --tags')

    def add_all(self):
        self.git('add .')
        self.git('add -u .')

    def add(self, path):
        self.git(f'add {path}')

    def commit(self, message):
        self.git(f'commit -m "{message}"')

    def git(self, command):
        return self.execute(f'git {command}')

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

        click.secho(f'[EXECUTE] {command}', fg='blue')
        captured = ''

        with Popen(
                command.split(),
                stdout=PIPE,
                stderr=STDOUT,
                bufsize=1,
                universal_newlines=True) as p:

            for line in p.stdout:
                captured += line
                click.secho(line, fg='white')

        return captured

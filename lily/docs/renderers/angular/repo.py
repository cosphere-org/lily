# -*- coding: utf-8 -*-

import shutil
import os
import re
from functools import partial
import tempfile

from lily.repo.repo import Repo
from lily.repo.version import VersionRenderer


class AngularRepo(Repo):

    origin = NotImplementedError

    def __init__(self, origin):
        self.origin = origin
        self.base_path = tempfile.mkdtemp()
        self.cd_to_repo()

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


class PathRule:

    def __init__(self, pattern, is_directory=False):
        self.pattern = re.compile(pattern, flags=re.I)
        self.is_directory = is_directory

    def matches(self, path):
        if self.is_directory and not os.path.isdir(path):
            return False

        return bool(self.pattern.search(path))


# FIXME: test it!!!
class TemplateRepo:

    # FIXME: move to settings!!!!!!
    origin = 'git@bitbucket.org:goodai/lily-angular-client.git'

    IGNORE_RULES = [
        PathRule(r'.*node_modules.*', True),
        PathRule(r'\.git$', True),
    ]

    KEEP_RULES = [
        PathRule(r'.*\.ts$'),
        PathRule(r'.*\.json$'),
        PathRule(r'.*\.html$'),
        PathRule(r'.*\.md$'),
        PathRule(r'.*\.ico$'),
        PathRule(r'.*karma.conf.js$'),
        PathRule(r'.*browserslist$'),
        PathRule(r'.*\.npmignore$'),
        PathRule(r'.*\.gitkeep$'),
        PathRule(r'.*\.css$'),
        PathRule(r'.*', True),  # keep all directories not explicitly ignored
    ]

    def __init__(self):
        self.base_path = tempfile.mkdtemp()
        self.cd_to_repo()

    def clone(self):
        super(TemplateRepo, self).clone(self.base_path)

    def copy_to(self, destination, client_prefix):

        shutil.copytree(
            self.base_path,
            destination,
            ignore=self.ignore,
            copy_function=partial(self.copy, client_prefix))

    def ignore(self, source, names):

        ignore_names = set([])
        for name in names:
            path = os.path.join(source, name)

            for ignore_rule in self.IGNORE_RULES:
                if ignore_rule.matches(path):
                    ignore_names.add(name)
                    break

            keep = False
            for keep_rule in self.KEEP_RULES:
                if keep_rule.matches(path):
                    keep = True
                    break

            if not keep:
                ignore_names.add(name)

        return list(ignore_names)

    def copy(self, client_prefix, source, destination):

        print('*** COPY ***>', client_prefix, source, destination)

        try:
            with open(source, 'r') as f:
                content = f.read()
                content = re.sub('__CLIENT_PREFIX__', client_prefix, content)

            with open(destination, 'w') as f:
                f.write(content)

        # -- binary data copying
        except UnicodeDecodeError:
            shutil.copy2(source, destination)

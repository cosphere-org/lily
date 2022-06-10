
import shutil
import os
import re
from functools import partial
import tempfile
import json
import collections
from subprocess import Popen, PIPE, STDOUT
import shlex
import click

from lily.shared import get_version, get_project_path
from lily.conf import settings


class Repo:

    def __init__(self):
        self.base_path = get_project_path()
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

    def add_all(self):
        self.git('add .')
        self.git('add -u .')

    def add(self, path):
        self.git(f'add {path}')

    def commit(self, message):
        self.git(f'commit --no-verify -m "{message}"')

    def all_changes_commited(self):
        changed = self.git('status --porcelain').strip()
        if changed:
            files = changed.split('\n')
            not_lily_changes = [f for f in files if '.lily/' not in f]

            return not bool(not_lily_changes)

        return True

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

        p = Popen(
            self.split_command(command),
            stdout=PIPE,
            stderr=STDOUT,
            bufsize=1,
            universal_newlines=True)

        while p.poll() is not None:
            line = p.stdout.readline()
            captured += line
            click.secho(line, fg='white')

        # -- final read
        line = p.stdout.read()
        captured += line
        click.secho(line, fg='white')

        # -- fetch return code
        p.communicate()
        if p.returncode != 0:
            raise OSError(
                f'Command: {command} return exit code: {p.returncode}')

        return captured

    def split_command(self, command):

        return shlex.split(command)


class AngularRepo(Repo):

    origin = NotImplementedError

    def __init__(self, origin):
        self.origin = origin
        self.base_path = tempfile.mkdtemp()

    def clone(self):
        super(AngularRepo, self).clone(self.base_path)

    def commit(self, version):
        self.git(f'commit -m "ADDED version {version}"')

    #
    # NPM
    #
    def build(self):
        self.npm('run build')

    def install(self):
        self.npm('install')

    def npm(self, command):
        self.execute(f'npm {command}')

    #
    # UTILS
    #
    def upgrade_version(self):

        # -- take only VERSION from here
        with open('projects/client/package.json', 'r') as p:
            packagejson = json.loads(p.read())
            next_version = (
                f'{get_version()}-API-{packagejson["version"]}-CLIENT')

        # -- take the whole configuration from here
        with open('package.json', 'r') as p:
            packagejson = json.loads(
                p.read(),
                object_pairs_hook=collections.OrderedDict)

        with open('package.json', 'w') as p:
            packagejson['version'] = next_version

            # -- final clean up
            try:
                del packagejson['main_ivy_ngcc']

            except KeyError:
                pass

            try:
                del packagejson['__processed_by_ivy_ngcc__']

            except KeyError:
                pass

            p.write(json.dumps(packagejson, indent=2))

        return next_version


class PathRule:

    def __init__(self, pattern, is_directory=False):
        self.pattern = re.compile(pattern, flags=re.I)
        self.is_directory = is_directory

    def matches(self, path):

        if self.is_directory:
            match = self.pattern.search(path)

            if match:
                parent_path = path[:match.end() + 1]

                return os.path.isdir(parent_path)

            else:
                return False

        return bool(self.pattern.search(path))


class TemplateRepo(Repo):

    origin = settings.LILY_ANGULAR_CLIENT_ORIGIN

    IGNORE_RULES = [
        PathRule(r'node_modules', True),
        PathRule(r'\.git', True),
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
        PathRule(r'.*\.gitignore$'),
        PathRule(r'.*\.css$'),
        PathRule(r'.*', True),  # keep all directories not explicitly ignored
    ]

    def __init__(self):
        self.base_path = tempfile.mkdtemp()

    def clone(self):
        super(TemplateRepo, self).clone(self.base_path)

    def copy_to(self, destination, client_prefix):

        ignore = self.ignore
        copy_function = partial(self.copy, client_prefix)

        def copytree(source, destination):
            """Replace `shutil.copytree` with overwrites."""

            if os.path.isdir(source):

                if not os.path.isdir(destination):
                    os.makedirs(destination)

                names = os.listdir(source)
                ignored = ignore(source, names)

                for name in names:
                    if name not in ignored:
                        copytree(
                            os.path.join(source, name),
                            os.path.join(destination, name))

            else:
                copy_function(source, destination)

        def rmtree(destination):

            for name in os.listdir(destination):
                remove = True
                path = os.path.join(destination, name)

                # -- ignore folders which should not be removed
                for ignore_rule in self.IGNORE_RULES:
                    if ignore_rule.matches(path):
                        remove = False
                        break

                if remove:
                    if os.path.isdir(path):
                        shutil.rmtree(path)

                    else:
                        os.remove(path)

        rmtree(destination)
        copytree(self.base_path, destination)

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

        try:
            with open(source, 'r') as f:
                content = f.read()
                content = re.sub('__CLIENT_PREFIX__', client_prefix, content)

            with open(destination, 'w') as f:
                f.write(content)

        # -- binary data copying
        except UnicodeDecodeError:
            shutil.copy2(source, destination)

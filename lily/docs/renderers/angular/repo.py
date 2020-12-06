
import shutil
import os
import re
from functools import partial
import tempfile
import json
import collections

from lily_assistant.repo.repo import Repo

from lily.conf import settings


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
    def upgrade_version(self, config):

        # -- take only VERSION from here
        with open('projects/client/package.json', 'r') as p:
            packagejson = json.loads(p.read())
            next_version = (
                f'{config.version}-API-{packagejson["version"]}-CLIENT')

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

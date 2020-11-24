
import shutil
import os
import re
from functools import partial
import tempfile

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
    # FIXME: allow here passing the version from the api gateway!!!
    # to have match between client version and API version
    # upgrades of the client itself, how can we control them???
    # -- maybe by adding extra API-<version>-CLIENT-<version>
    def upgrade_version(self, config):

        with open('package.json', 'r') as p:
            conf = p.read()
            version_match = re.search(
                r'\"version\"\:\s\"(?P<version>[\d\.]+)\"', conf, re.M)
            version = version_match.groupdict()['version']
            span = version_match.span()

            api_version = config.version
            next_version = f'{api_version}-API-{version}-CLIENT'

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

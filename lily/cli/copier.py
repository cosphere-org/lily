
import os
import re

import click

from lily.base.conf import Config
from lily import __version__


class Copier:

    class NotProjectRootException(Exception):
        pass

    def __init__(self):
        self.root_dir = os.getcwd()

    def copy(self, src_dir):

        self.create_empty_config(src_dir)

        self.copy_makefile(src_dir)

    def create_empty_config(self, src_dir):

        if not Config.exists():
            Config.create_empty(src_dir)

    def copy_makefile(self, src_dir):

        current_version = __version__

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # noqa

        # lily_path =
        # if not os.path.exists(lily_path):
        #     os.mkdir(lily_path)
        with open(os.path.join(BASE_DIR, 'lily.makefile'), 'r') as makefile:
            content = makefile.read()
            content = re.sub(r'{%\s*SRC_DIR\s*%}', src_dir, content)
            content = re.sub(r'{%\s*VERSION\s*%}', current_version, content)

        if not os.path.exists(os.path.join(self.root_dir, '.lily')):
            os.mkdir(os.path.join(self.root_dir, '.lily'))

        makefile_path = os.path.join(
            self.root_dir, '.lily', 'lily.makefile')

        with open(makefile_path, 'w') as f:
            f.write(content)

        click.secho(
            'copied lily makefile to {makefile_path}'.format(
                makefile_path=makefile_path),
            fg='blue')


import os
import re

import click
from lily_assistant.config import Config


class Copier:

    def __init__(self):
        self.root_dir = os.getcwd()

    def copy(self, src_dir):

        self.copy_makefile(src_dir)

    def copy_makefile(self, src_dir):

        config = Config()

        with open(self.base_makefile_path, 'r') as makefile:
            content = makefile.read()
            content = re.sub(r'{%\s*SRC_DIR\s*%}', src_dir, content)
            content = re.sub(r'{%\s*VERSION\s*%}', config.version, content)

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

    @property
    def base_makefile_path(self):

        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'base.makefile')

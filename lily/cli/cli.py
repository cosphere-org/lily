
import os
import textwrap

import click

from .copier import Copier
from .logger import Logger


logger = Logger()


if not os.environ.get('LC_ALL'):  # pragma: no cover
    os.environ['LC_ALL'] = 'en_US.utf-8'


if not os.environ.get('LANG'):  # pragma: no cover
    os.environ['LANG'] = 'en_US.utf-8'


@click.group()
def cli():
    pass


@click.command()
@click.argument('src_dir')
def init(src_dir):
    """Init `lily` with some preliminary files copying and creation.

    Init `Lily`. During this operation the following will take place:
    - `.lily/lily.makefile` will be copied to the root project directory.

    WARNING it is assumed that this command will be invoked in the root
    of the project.

    :param src_dir: name of your source directory

    """

    if not os.path.exists(os.path.join(os.getcwd(), '.lily', 'config.json')):
        raise click.ClickException(textwrap.dedent('''
            Please run `lily init <src_dir>`
        '''))

    Copier().copy(src_dir)

    logger.info('''

        Please insert the following line at the top of your Makefile:

        include .lily/lily.makefile
    ''')


cli.add_command(init)

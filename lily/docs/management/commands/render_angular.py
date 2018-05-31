# -*- coding: utf-8 -*-

import djclick as click

from ...renderers.angular.renderer import AngularClientRenderer
from lily.base.utils import normalize_indentation


@click.command()
@click.option(
    '--only_build',
    default=False,
    type=click.BOOL,
    help='if true it only builds the client without pushing it to the remote')
def command(only_build):
    """
    Render Angular Client based on the command definitions of all
    registered services.

    """
    rendered_version = AngularClientRenderer().render(only_build=only_build)

    if only_build:
        click.secho(normalize_indentation('''
            - Successfully rendered and built Angular Client [NO PUSHING TO REMOTE]
        ''', 0), fg='green')  # noqa

    else:
        click.secho(normalize_indentation('''
            - Successfully rendered and pushed Angular Client version: {version}
        '''.format(version=rendered_version), 0), fg='green')  # noqa

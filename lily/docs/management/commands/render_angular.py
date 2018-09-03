# -*- coding: utf-8 -*-

import djclick as click

from ...renderers.angular.renderer import AngularClientRenderer
from lily.base.utils import normalize_indentation


@click.command()
@click.argument(
    'client_origin',
    type=str,
    help='the origin of repo into which rendered client should be pushed')
@click.argument(
    'client_prefix',
    type=str,
    help='the prefix of client')
@click.option(
    '--only_build',
    default=False,
    type=click.BOOL,
    help='if true it only builds the client without pushing it to the remote')
@click.option(
    '--include_domain',
    '-i',
    type=str,
    multiple=True,
    help='provide domains to include')
@click.option(
    '--exclude_domain',
    '-e',
    type=str,
    multiple=True,
    help='provide domains to exclude')
def command(only_build, include_domain, exclude_domain):
    """
    Render Angular Client based on the command definitions of all
    registered services.

    """
    rendered_version = AngularClientRenderer().render(
        only_build=only_build,
        include_domains=include_domain,
        exclude_domains=exclude_domain)

    if only_build:
        click.secho(normalize_indentation('''
            - Successfully rendered and built Angular Client [NO PUSHING TO REMOTE]
        ''', 0), fg='green')  # noqa

    else:
        click.secho(normalize_indentation('''
            - Successfully rendered and pushed Angular Client version: {version}
        '''.format(version=rendered_version), 0), fg='green')  # noqa

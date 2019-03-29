
import djclick as click

from ...renderers.angular.renderer import AngularClientRenderer
from lily.base.utils import normalize_indentation


@click.command()
@click.argument(
    'client_origin',
    type=str)
@click.argument(
    'client_prefix',
    type=str)
@click.option(
    '--only_build',
    default=False,
    is_flag=True,
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
def command(
        client_origin,
        client_prefix,
        only_build,
        include_domain,
        exclude_domain):
    """Render Angular Client based on the declared commands."""

    rendered_version = AngularClientRenderer(
        client_origin, client_prefix
    ).render(
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

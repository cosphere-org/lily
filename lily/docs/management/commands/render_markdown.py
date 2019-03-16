
import djclick as click

from importlib import import_module
import os

from lily.conf import settings
from lily.base.config import Config
from ...renderers.markdown.renderer import MarkdownRenderer


@click.command()
def command():
    """Render Markdown Specification for all registered Commands."""

    urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns

    with open(os.path.join(Config.get_lily_path(), 'API.md'), 'w') as f:
        f.write(MarkdownRenderer(urlpatterns).render())

    click.secho(
        'Successfully rendered Markdown Specification for all '
        'registered Commands',
        fg='green')

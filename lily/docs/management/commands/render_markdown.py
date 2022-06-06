
import os
import sys
from importlib import import_module

import djclick as click

from lily.conf import settings
from lily.shared import get_lily_path
from ...renderers.markdown.renderer import MarkdownRenderer


@click.command()
def command():
    """Render Markdown Specification for all registered Commands."""

    # -- make sure that the main directory is also visible during
    # -- the search of all url patterns
    sys.path.insert(0, os.getcwd())

    urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns

    with open(os.path.join(get_lily_path(), 'API.md'), 'w') as f:
        f.write(MarkdownRenderer(urlpatterns).render())

    click.secho(
        'Successfully rendered Markdown Specification for all '
        'registered Commands',
        fg='green')

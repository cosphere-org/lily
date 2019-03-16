
from importlib import import_module
import os

from django.core.management.base import BaseCommand

from lily.conf import settings
from lily.base.conf import Config
from ...renderers.markdown import MarkdownRenderer


class Command(BaseCommand):
    help = 'Render Markdown Specification for all registered Commands'

    def save_to_file(self, content):

        with open(os.path.join(Config.get_lily_path(), 'API.md'), 'w') as f:
            f.write(content)

    def handle(self, *args, **options):

        urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns

        self.save_to_file(MarkdownRenderer(urlpatterns).render())

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully rendered Markdown Specification for all '
                'registered Commands'))

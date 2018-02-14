# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings

from conf.urls_api import urlpatterns
from ...markdown_renderer import Renderer as MarkdownRenderer


class Command(BaseCommand):
    help = 'Render Markdown Specification for all registered Commands'

    def save_to_file(self, filename, content):
        with open(filename, 'w') as f:
            f.write(content)

    def handle(self, *args, **options):

        self.save_to_file(
            settings.DOCS_MARKDOWN_SPEC_FILE,
            MarkdownRenderer(urlpatterns).render())

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully rendered Markdown Specification for all '
                'registered Commands'))

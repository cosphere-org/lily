# -*- coding: utf-8 -*-

from importlib import import_module

from django.core.management.base import BaseCommand
from django.conf import settings

from ...markdown_renderer import Renderer as MarkdownRenderer


class Command(BaseCommand):
    help = 'Render Markdown Specification for all registered Commands'

    def save_to_file(self, filename, content):
        with open(filename, 'w') as f:
            f.write(content)

    def handle(self, *args, **options):

        urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns
        self.save_to_file(
            settings.LILY_DOCS_MARKDOWN_SPEC_FILE,
            MarkdownRenderer(urlpatterns).render())

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully rendered Markdown Specification for all '
                'registered Commands'))

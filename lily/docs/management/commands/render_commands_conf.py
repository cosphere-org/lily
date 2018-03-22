# -*- coding: utf-8 -*-

from importlib import import_module
import json

from django.core.management.base import BaseCommand
from django.conf import settings

from ...commands_conf_renderer import CommandsConfRenderer


class Command(BaseCommand):
    help = 'Render Commands Configuration for all registered Commands'

    def save_to_file(self, filename, views_index):
        with open(filename, 'w') as f:
            f.write(json.dumps(views_index, indent=4))

    def handle(self, *args, **options):
        urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns

        self.save_to_file(
            settings.LILY_DOCS_COMMANDS_CONF_FILE,
            CommandsConfRenderer(urlpatterns).render())

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully rendered Commands Configuration for all '
                'registered Commands'))

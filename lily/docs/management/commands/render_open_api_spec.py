
from importlib import import_module
import json

from django.core.management.base import BaseCommand
import yaml

from lily.conf import settings
from ...open_api_renderer import Renderer as OpenAPIRenderer


class Command(BaseCommand):
    help = 'Render Open API specification for all registered Commands'

    def save_to_file(self, filename, content):
        with open(filename, 'w') as f:
            f.write(json.dumps(yaml.load(content), indent=4))

    def handle(self, *args, **options):
        urlpatterns = import_module(settings.ROOT_URLCONF).urlpatterns

        self.save_to_file(
            settings.LILY_DOCS_OPEN_API_SPEC_FILE,
            OpenAPIRenderer(urlpatterns).render())

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully rendered Open API Specification for all '
                'registered Commands'))

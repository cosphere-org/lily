# -*- coding: utf-8 -*-

import json
import os

from django.views.generic import View

from base.events import JsonResponse


BASE_DIR = os.path.dirname(__file__)


class OpenAPISpecView(View):

    def get(self, service_name):
        spec_path = os.path.join(BASE_DIR, 'open_api_spec.json')
        with open(spec_path, 'r') as f:
            return JsonResponse(json.loads(f.read()))

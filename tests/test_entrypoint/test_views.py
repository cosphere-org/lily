# -*- coding: utf-8 -*-

from django.test import TestCase, override_settings
from django.urls import reverse

from base.test import Client


class EntryPointViewTestCase(TestCase):

    uri = reverse('entrypoint:entrypoint')

    def setUp(self):

        self.app = Client()
        self.auth_headers = {
            'HTTP_X_CS_ACCOUNT_TYPE': 'WHATEVER',
            'HTTP_X_CS_USER_ID': 190,
        }

    @override_settings(
        LILY_SERVICE_VERSION='2.5.6',
        LILY_SERVICE_NAME='some service')
    def test_get_200(self):

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'version': '2.5.6',
        }

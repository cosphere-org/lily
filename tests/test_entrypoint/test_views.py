# -*- coding: utf-8 -*-

from django.test import TestCase
from django.urls import reverse
import pytest
from mock import Mock

from lily.base.test import Client


class EntryPointViewTestCase(TestCase):

    uri = reverse('entrypoint:entrypoint')

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):

        self.app = Client()
        self.auth_headers = {
            'HTTP_X_CS_ACCOUNT_TYPE': 'WHATEVER',
            'HTTP_X_CS_USER_ID': 190,
        }

    def test_get_200(self):

        self.mocker.patch('entrypoint.views.config', Mock(version='2.5.6'))

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@event': 'ENTRY_POINT_READ',
            '@type': 'entrypoint',
            'version': '2.5.6',
        }

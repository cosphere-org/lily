# -*- coding: utf-8 -*-

from django.test import TestCase
from django.urls import reverse
import pytest
from mock import Mock, call

from lily.base.test import Client


class EntryPointViewTestCase(TestCase):

    uri = reverse('entrypoint:entrypoint')

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        self.app = Client()
        self.auth_headers = {
            'HTTP_X_CS_ACCOUNT_TYPE': 'ADMIN',
            'HTTP_X_CS_USER_ID': 190,
        }

    def test_get(self):

        self.mocker.patch('entrypoint.views.config', Mock(version='2.5.6'))

        renderer = self.mocker.patch('entrypoint.views.CommandsRenderer')
        render = Mock(return_value={'some': 'spec'})
        renderer.return_value = Mock(render=render)
        urlpatterns = Mock()
        self.mocker.patch(
            'entrypoint.views.EntryPointView.get_urlpatterns',
        ).return_value = urlpatterns

        response = self.app.get(self.uri, **self.auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            '@type': 'entrypoint',
            '@event': 'ENTRY_POINT_READ',
            'version': '2.5.6',
            'commands': {'some': 'spec'},
        }
        assert renderer.call_args_list == [call(urlpatterns)]

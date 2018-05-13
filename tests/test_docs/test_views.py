# -*- coding: utf-8 -*-

from django.test import TestCase
from django.urls import reverse
import pytest
from mock import Mock, call

from lily.base.test import Client


class TypeScriptSpecViewCase(TestCase):

    uri = reverse('docs:typescript_spec')

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

        renderer = self.mocker.patch('docs.views.TypeScriptSpecRenderer')
        render = Mock(return_value={'some': 'spec'})
        renderer.return_value = Mock(render=render)
        urlpatterns = Mock()
        self.mocker.patch(
            'docs.views.TypeScriptSpecView.get_urlpatterns',
        ).return_value = urlpatterns

        respose = self.app.get(self.uri, **self.auth_headers)

        assert respose.status_code == 200
        assert respose.json() == {
            '@type': 'typescript_spec',
            '@event': 'TYPESCRIPT_SPEC_READ',
            'spec': {'some': 'spec'},
        }
        assert renderer.call_args_list == [call(urlpatterns)]

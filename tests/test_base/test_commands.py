
from unittest.mock import call

from django.test import TestCase, override_settings
from django.urls import re_path, reverse
import pytest
from conf.urls import urlpatterns

from lily.base.test import Client
from lily.base.commands import S3UploadSignCommands
from lily.base.command import command_override
from lily import (
    Meta,
    name,
    Domain,
    Access,
)


MySignCommands = S3UploadSignCommands.overwrite(
    get=command_override(
        name=name.Execute('SIGN', 'PROCESS'),
        meta=Meta(
            title=(
                'Sign Process dedicated to upload and conversion of media '
                'file'),
            domain=Domain(id='hey', name='hi')),
        access=Access(
            access_list=['PREMIUM', 'SUPER_PREMIUM'])))


urlpatterns.extend([
    re_path(r'^sign/$', MySignCommands.as_view(), name='test.sign'),

])


class MySignCommandsTestCase(TestCase):

    uri = reverse('test.sign')

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def setUp(self):
        self.app = Client()
        self.user_id = 56
        self.auth_headers = {
            'HTTP_X_CS_ACCOUNT_TYPE': 'PREMIUM',
            'HTTP_X_CS_USER_ID': self.user_id,
        }

    @override_settings(AWS_S3_ACCESS_KEY="access.key", AWS_S3_REGION="central")
    def test_get_200(self):

        sign_mock = self.mocker.patch.object(MySignCommands, 'sign')
        sign_mock.side_effect = [
            'signature 1', 'signature 2', 'signature 3', 'signature 4',
        ]
        get_signature_mock = self.mocker.patch.object(
            MySignCommands, 'get_signature')
        get_signature_mock.return_value = "af52522c5afb83b5348ed06b5fbd0c"

        response = self.app.get(
            self.uri,
            data={
                "to_sign": "hi there",
                "datetime": "20171201T123112Z",
            },
            **self.auth_headers)

        assert response.status_code == 200
        assert response.content == b"af52522c5afb83b5348ed06b5fbd0c"
        assert (
            get_signature_mock.call_args_list ==
            [call('signature 4', 'hi there')])
        assert (
            sign_mock.call_args_list == [
                call(b'AWS4access.key', '20171201'),
                call('signature 1', 'central'),
                call('signature 2', 's3'),
                call('signature 3', 'aws4_request'),
            ])

    def test_get_400__missing_fields(self):

        # -- missing to sign
        response = self.app.get(
            self.uri,
            data={"datetime": "20171201T123112Z"},
            **self.auth_headers)

        assert response.status_code == 400
        assert response.json() == {
            '@event': 'QUERY_DID_NOT_VALIDATE',
            '@type': 'error',
            'errors': {'to_sign': ['This field is required.']},
            '@authorizer': {
                'account_type': 'PREMIUM',
                'user_id': self.user_id,
            }
        }

        # -- missing datetime
        response = self.app.get(
            self.uri,
            data={"to_sign": "hi there"},
            **self.auth_headers)

        assert response.status_code == 400
        assert response.json() == {
            '@event': 'QUERY_DID_NOT_VALIDATE',
            '@type': 'error',
            'errors': {'datetime': ['This field is required.']},
            '@authorizer': {
                'account_type': 'PREMIUM',
                'user_id': self.user_id,
            },
        }

    def test_get_400__broken_datetime(self):

        response = self.app.get(
            self.uri,
            data={
                "to_sign": "hi there",
                "datetime": "2017000001201T123112Z",
            },
            **self.auth_headers)

        assert response.status_code == 400
        assert response.json() == {
            '@event': 'QUERY_DID_NOT_VALIDATE',
            '@type': 'error',
            'errors': {
                'datetime': [(
                    'invalid datetime format accepted is YYYYMMDDThhmmssZ'
                )]
            },
            '@authorizer': {
                'account_type': 'PREMIUM',
                'user_id': self.user_id,
            },
        }

# -*- coding: utf-8 -*-

from datetime import datetime
import string

from mock import Mock, call
from itsdangerous import SignatureExpired

from lily.base import signature
from lily.base.events import EventFactory


#
# sign_payload
#
def test_sign_payload__calls_dumps_correctly(mocker):

    serializer_class_mock = mocker.patch(
        'base.signature.URLSafeTimedSerializer')

    signature.sign_payload(
        email='test@whats.com',
        payload='WHATEVER',
        secret='personal_secret',
        salt='salt_me')

    assert serializer_class_mock.call_args_list == [call('personal_secret')]
    assert (
        serializer_class_mock.return_value.dumps.call_args_list ==
        [call(['test@whats.com', 'WHATEVER'], salt='salt_me')])


def test_sign_payload__returns_correct_code(mocker):

    serializer_class_mock = mocker.patch(
        'base.signature.URLSafeTimedSerializer')
    serializer_class_mock.return_value = Mock(
        dumps=Mock(return_value='g67g6f7g'))

    encoded_payload = signature.sign_payload(
        email='test@whats.com',
        payload='WAT',
        secret='personal_secret',
        salt='salt_me')

    assert encoded_payload == 'g67g6f7g'


#
# verify_payload
#
def test_verify_payload__make_the_right_calls(mocker):

    serializer_class_mock = mocker.patch(
        'base.signature.URLSafeTimedSerializer')
    serializer_class_mock.return_value.loads.return_value = ('hi@there', 'HI')

    signature.verify_payload(
        encoded_payload='rubishtokenwhereareyou',
        secret='my_secret',
        salt='salt_me',
        signer_email='hi@there',
        max_age=24)

    assert serializer_class_mock.call_args_list == [call('my_secret')]
    assert (
        serializer_class_mock.return_value.loads.call_args_list ==
        [call('rubishtokenwhereareyou', salt='salt_me', max_age=24)])


def test_verify_payload__different_secrets_for_encoding_and_decoding():

    code = signature.sign_payload(
        'why@gmail.com', 'NO!', 'secret123', 'salt')

    try:
        assert signature.verify_payload(
            code, 'my_secret', 'salt', 'hi@there', 120)

    except EventFactory.BrokenRequest as e:
        assert e.event == 'PAYLOAD_VERIFIED_AS_BROKEN'

    else:
        raise AssertionError


def test_verify_payload__email_mismatch(mocker):

    code = signature.sign_payload(
        'why@gmail.com', 'NO!', 'secret123', 'salt')

    try:
        assert signature.verify_payload(
            code, 'secret123', 'salt', 'hello@there', 120)

    except EventFactory.BrokenRequest as e:
        assert e.event == 'PAYLOAD_VERIFIED_AS_BROKEN_MISMATCHING_EMAILS'

    else:
        raise AssertionError


def test_verify_payload__recognizes_expired_token(mocker):

    serializer_class_mock = mocker.patch(
        'base.signature.URLSafeTimedSerializer')
    logger_mock = mocker.patch(
        'base.signature.logger')
    serializer_class_mock.return_value = Mock(
        dumps=Mock(return_value='TeStM3OuT'),
        loads=Mock(side_effect=SignatureExpired(
            'error occured', date_signed=datetime(2013, 1, 15, 6, 48))),
        loads_unsafe=Mock(return_value=(None, ['test@whats.com', 'HI!'])),
    )

    code = signature.sign_payload(
        'test@whats.com', 'HI!', 'personal_secret', 'salt')
    try:
        payload = signature.verify_payload(
            code, 'personal_secret', 'salt', 'test@whats.com', 24)

        assert payload == 'HI!'
        assert logger_mock.info.call_args_list == [
            call('Code expired for email: test@whats.com, '
                 'signed at: 2013-01-15 06:48:00')]

    except EventFactory.BrokenRequest as e:
        assert e.event == 'PAYLOAD_VERIFIED_AS_EXPIRED'

    else:
        raise AssertionError


#
# create_secret
#
def test_create_secret__creates_unique_secrets():

    secrets = [signature.create_secret() for i in range(1000)]

    assert len(secrets) == len(set(secrets))


def test_create_secret__safe_secret():

    def assert_is_secret_safe(secret):
        assert len(secret) == 64

        assert len(set(string.ascii_uppercase) & set(secret)) > 0
        assert len(set(string.ascii_lowercase) & set(secret)) > 0
        assert len(set(string.digits) & set(secret)) > 0
        assert len(set(string.punctuation) & set(secret)) > 0

        # uniqueness of characters
        assert len(set(secret)) > 32

    for i in range(1000):
        assert_is_secret_safe(signature.create_secret())

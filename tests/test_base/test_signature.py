
from datetime import datetime
import string
from unittest.mock import call

from itsdangerous import SignatureExpired, URLSafeTimedSerializer
import pytest

from lily.base import signature
from lily.base.events import EventFactory


#
# sign_payload
#
def test_sign_payload__calls_dumps_correctly(mocker):

    dumps_mock = mocker.patch.object(URLSafeTimedSerializer, 'dumps')

    signature.sign_payload(
        email='test@whats.com',
        payload='WHATEVER',
        secret='personal_secret',
        salt='salt_me')

    assert dumps_mock.call_args_list == [
        call(['test@whats.com', 'WHATEVER'], salt='salt_me')]


def test_sign_payload__returns_correct_code(mocker):

    mocker.patch.object(
        URLSafeTimedSerializer, 'dumps').return_value = 'g67g6f7g'

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

    loads_mock = mocker.patch.object(URLSafeTimedSerializer, 'loads')
    loads_mock.return_value = ('hi@there', 'HI')

    payload = signature.verify_payload(
        encoded_payload='rubishtokenwhereareyou',
        secret='my_secret',
        salt='salt_me',
        signer_email='hi@there',
        max_age=24)

    assert payload == 'HI'
    assert loads_mock.call_count == 1


def test_verify_payload__different_secrets_for_encoding_and_decoding():

    code = signature.sign_payload(
        'why@gmail.com', 'NO!', 'secret123', 'salt')

    with pytest.raises(EventFactory.BrokenRequest) as e:
        assert signature.verify_payload(
            code, 'my_secret', 'salt', 'hi@there', 120)

    assert e.value.event == 'PAYLOAD_VERIFIED_AS_BROKEN'


def test_verify_payload__email_mismatch(mocker):

    code = signature.sign_payload(
        'why@gmail.com', 'NO!', 'secret123', 'salt')

    with pytest.raises(EventFactory.BrokenRequest) as e:
        signature.verify_payload(
            code, 'secret123', 'salt', 'hello@there', 120)

    assert e.value.event == 'PAYLOAD_VERIFIED_AS_BROKEN_MISMATCHING_EMAILS'


def test_verify_payload__recognizes_expired_token(mocker):

    mocker.patch.object(
        URLSafeTimedSerializer,
        'loads'
    ).side_effect = SignatureExpired(
        'error occured',
        date_signed=datetime(2013, 1, 15, 6, 48))

    with pytest.raises(EventFactory.BrokenRequest) as e:
        signature.verify_payload(
            'what.ever', 'personal_secret', 'salt', 'test@whats.com', 24)

    assert e.value.event == 'PAYLOAD_VERIFIED_AS_EXPIRED'


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
        assert len(set(secret)) > 30

    for i in range(1000):
        assert_is_secret_safe(signature.create_secret())


from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone
import pytest

from lily.base import serializers
from .serializers import (
    AccountPlainSerializer,
    PersonSerializer,
    PersonModelSerializer,
    AccountSerializer,
    MediaItemFileSerializer,
    MediaItemSerializer,
)
from .models import Account, Person, MediaItemFile


class SerializerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker):
        self.mocker = mocker

    #
    # CASE: SIMPLE SERIALIZER
    #
    def test_serialize__simple_serializer(self):

        assert AccountPlainSerializer({
            'user_id': 11,
            'avatar_uri': 'this is avatar',
            'username': 'Jack'
        }).data == {
            '@type': 'account_plain',
            'user_id': 11,
            'avatar_uri': 'this is avatar',
            'username': 'Jack'
        }

    #
    # CASE: SIMPLE SERIALIZER WITH ACCESS
    #
    def test_serialize__simple_serializer_with_empty_access(self):

        p = Person(name='John', age=81)

        self.mocker.patch.object(
            PersonSerializer, 'get_access').return_value = []

        assert PersonSerializer(
            p, context={'request': Mock()}
        ).data == {
            '@type': 'person',
            'age': 81,
            'name': 'John',
        }

    def test_serialize__simple_serializer_with_access(self):

        p = Person(name='John', age=81)

        assert PersonSerializer(
            p, context={'request': Mock()}
        ).data == {
            '@type': 'person',
            '@access': {
                'MARK_IT': True,
                'REMOVE_IT': False,
                'ALLOW_IT': False,
            },
            'age': 81,
            'name': 'John',
        }

    #
    # CASE: SIMPLE MODEL SERIALIZER WITH ACCESS
    #
    def test_serialize__simple_model_serializer_with_empty_access(self):

        p = Person(name='John', age=81)

        self.mocker.patch.object(
            PersonModelSerializer, 'get_access').return_value = []

        assert PersonModelSerializer(
            p, context={'request': Mock()}
        ).data == {
            '@type': 'person',
            'age': 81,
            'name': 'John',
        }

    def test_serialize__simple_model_serializer_with_access(self):

        p = Person(name='John', age=81)

        assert PersonModelSerializer(
            p, context={'request': Mock()}
        ).data == {
            '@type': 'person',
            '@access': {
                'MARK_IT': True,
                'REMOVE_IT': False,
                'ALLOW_IT': False,
            },
            'age': 81,
            'name': 'John',
        }

    #
    # CASE: MODEL SERIALIZER WITH ENUM & SERIALIZER METHOD FIELD
    #
    def test_serialize__model_serializer_with_enum_and_method(self):

        now = timezone.now()
        a = Account(
            user_id=11,
            atype='FREE',
            freemium_till_datetime=now,
            show_in_ranking=True)
        a.user_email = 'jack@player.io'

        assert AccountSerializer(
            a, context={'request': Mock(access={'user_id': 11})}
        ).data == {
            '@type': 'account',
            'user_id': 11,
            'atype': 'FREE',
            'freemium_till_datetime': now.isoformat().replace('+00:00', 'Z'),
            'show_in_ranking': True,
            'email': 'jack@player.io',
        }

    #
    # CASE: NESTED SERIALIZERS AND MANY
    #
    def test_serialize__nested_serializer_and_many(self):

        f0 = MediaItemFile(
            content_type='image/png',
            file_uri='http://image.png')
        f1 = MediaItemFile(
            content_type='image/jpg',
            file_uri='http://image.jpg')
        f2 = MediaItemFile(
            content_type='image/gif',
            file_uri='http://image.gif')

        m = {
            'id': 21,
            'original': f0,
            'files': [f1, f2],
            'type': 'IMAGE',
            'usage_type': 'MEDIAITEM',
            'text': 'hello world',
            'reference': {
                'what': 'is it?',
            }
        }

        assert MediaItemSerializer(m).data == {
            '@type': 'mediaitem',
            'id': 21,
            'original': MediaItemFileSerializer(f0).data,
            'files': [
                MediaItemFileSerializer(f1).data,
                MediaItemFileSerializer(f2).data,
            ],
            'type': 'IMAGE',
            'usage_type': 'MEDIAITEM',
            'text': 'hello world',
            'reference': {
                'what': 'is it?',
            }
        }


class EmptySerializerTestCase(TestCase):

    def test__passes_nothing(self):

        s = serializers.EmptySerializer({'hi': 'there'})

        assert s.data == {'@type': 'empty'}


class AbstractSerializerTestCase(TestCase):

    def test_type_not_needed(self):

        class AbstractCustomer(serializers.AbstractSerializer):

            name = serializers.CharField()

        assert AbstractCustomer({'name': 'Jack'}).data == {'name': 'Jack'}


class ObjectSerializerTestCase(TestCase):

    def test__passes_everything(self):

        s = serializers.ObjectSerializer({'hi': 'there'})

        assert s.data == {
            '@type': 'object',
            'hi': 'there',
        }


class CommandSerializerTestCase(TestCase):

    def test_serializes_command_correctly(self):

        s = serializers.CommandSerializer({
            'name': 'DO_IT',
            'method': 'post',
            'uri': 'http://do.it/now',
            'body': {'wat': 'yes'},
        })

        assert s.data == {
            '@type': 'command',
            'name': 'DO_IT',
            'method': 'post',
            'uri': 'http://do.it/now',
            'body': {'wat': 'yes'},
            'query': None,
            'result': None
        }

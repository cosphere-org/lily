
from unittest.mock import Mock

from django.test import TestCase
from django.db import models
import pytest

from lily.base import serializers


#
# Test Serializers
#
class Customer(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    class Meta:
        app_label = 'base'


class CustomerSerializer(serializers.Serializer):

    _type = 'customer'

    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)

    def get_access(self, instance):

        return [
            (Mock(command_conf={'name': 'MARK_IT'}), True),
            (Mock(command_conf={'name': 'REMOVE_IT'}), False),
            ('ALLOW_IT', False),
        ]


class CustomerModelSerializer(serializers.ModelSerializer):

    _type = 'customer'

    def get_access(self, instance):

        return [
            (Mock(command_conf={'name': 'MARK_IT'}), True),
            (Mock(command_conf={'name': 'REMOVE_IT'}), False),
            ('ALLOW_IT', False),
        ]

    class Meta:
        model = Customer
        fields = ('name', 'age')


class SerializerTestCase(TestCase):

    serializer = CustomerSerializer

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker):
        self.mocker = mocker

    def test_to_internal_value(self):

        class MetaCustomer(serializers.Serializer):
            _type = 'customer'
            at__name = serializers.CharField()
            at__age = serializers.IntegerField()
            is_ready = serializers.BooleanField()

        s = MetaCustomer(data={
            '@name': 'George',
            '@age': 13,
            'is_ready': False,
        })

        assert s.is_valid() is True
        assert s.data == {
            '@type': 'customer',
            '@name': 'George',
            '@age': 13,
            'is_ready': False,
        }

    def test_to_internal_value_with_instance(self):

        class WhatSerializer(serializers.Serializer):
            what = serializers.IntegerField()

        class MetaCustomer(serializers.Serializer):
            _type = 'customer'
            name = serializers.CharField()
            age = serializers.IntegerField()
            is_ready = serializers.BooleanField()
            what = WhatSerializer()

        data = {
            'name': 'George',
            'age': 13,
            'is_ready': False,
            'what': ['what'],
        }
        s = MetaCustomer(data=data)

        assert dict(s.to_internal_value(data)) == {
            'name': 'George',
            'age': 13,
            'is_ready': False,
            'what': ['what'],
        }

    def test_to_representation__without_access(self):

        p = Customer(name='John', age=81)

        self.mocker.patch.object(
            self.serializer, 'get_access').return_value = []

        assert self.serializer(
            context={'request': Mock(), 'command_name': 'ACT_NOW'}
        ).to_representation(p) == {
            '@type': 'customer',
            'age': 81,
            'name': 'John',
        }

    def test_to_representation__with_access(self):

        p = Customer(name='John', age=81)

        assert self.serializer(
            context={'request': Mock(), 'command_name': 'ACT_NOW'}
        ).to_representation(p) == {
            '@type': 'customer',
            '@access': {
                'MARK_IT': True,
                'REMOVE_IT': False,
                'ALLOW_IT': False,
            },
            'age': 81,
            'name': 'John',
        }


class ModelSerializerTestCase(SerializerTestCase):

    serializer = CustomerModelSerializer


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

        s = serializers.CommandSerializer(data={
            'name': 'DO_IT',
            'method': 'post',
            'uri': 'http://do.it/now',
            'body': {'wat': 'yes'},
        })

        assert s.is_valid() is True
        assert s.data == {
            '@type': 'command',
            'name': 'DO_IT',
            'method': 'post',
            'uri': 'http://do.it/now',
            'body': {'wat': 'yes'},
        }

    def test__fails_on_invalid_input(self):
        s = serializers.CommandSerializer(data={
            'name': 'hi there',
            'uri': 'not url',
        })

        assert s.is_valid() is False
        assert s.errors == {
            'method': ['This field is required.'],
            'uri': ['Enter a valid URL.'],
        }

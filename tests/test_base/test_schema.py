# -*- coding: utf-8 -*-

from django.test import TestCase
from django.db import models

from lily.base import serializers, parsers
from lily.base.schema import to_schema


class Person(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    class Meta:
        app_label = 'base'


class PersonQueryParser(parsers.QueryParser):
    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class PersonBodyParser(parsers.BodyParser):
    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class PersonSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class PersonModelSerializer(serializers.ModelSerializer):
    is_underaged = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ('name', 'age', 'is_ready', 'is_underaged')

    def get_is_underaged(self, instance) -> bool:
        return instance.age > 18


class ProviderSerializer(serializers.Serializer):
    name = serializers.CharField(default='Johnny')


class FoodSerializer(serializers.Serializer):

    provider = ProviderSerializer()

    amount = serializers.IntegerField()


class PartySerializer(serializers.Serializer):

    guests = PersonSerializer(many=True)

    host = PersonModelSerializer()

    food = FoodSerializer()


class SerializerToSchemaTestCase(TestCase):

    def test_one_can_call_it_with_class_or_instance(self):

        assert (
            to_schema(PersonSerializer) ==
            to_schema(PersonSerializer()))

    #
    # Body Parser
    #
    def test_person_body_parser(self):

        assert to_schema(PersonBodyParser) == {
            'type': 'object',
            'required': ['age'],
            'properties': {
                'age': {
                    'type': 'number',
                    'minimum': 18,
                },
                'name': {
                    'type': 'string',
                    'maxLength': 123,
                },
            },
        }

    def test_person_query_parser(self):

        assert to_schema(PersonQueryParser) == {
            'type': 'object',
            'required': ['age'],
            'properties': {
                'age': {
                    'type': 'number',
                    'minimum': 18,
                },
                'name': {
                    'type': 'string',
                    'maxLength': 123,
                },
            },
        }

    #
    # Serializer
    #
    def test_person_serializer(self):

        assert to_schema(PersonSerializer) == {
            'type': 'object',
            'required': ['age'],
            'properties': {
                'age': {
                    'type': 'number',
                    'minimum': 18,
                },
                'name': {
                    'type': 'string',
                    'maxLength': 123,
                },
            },
        }

    #
    # Model Serializer
    #
    def test_person_model_serializer(self):

        assert to_schema(PersonModelSerializer) == {
            'type': 'object',
            'required': ['name', 'is_underaged'],
            'properties': {
                'name': {
                    'type': 'string',
                    'maxLength': 100,
                },
                'age': {
                    'type': 'number',
                },
                'is_underaged': {
                    'type': 'boolean',
                },
                'is_ready': {
                    'type': 'boolean',
                },
            },
        }

    #
    # Method Derived Serializer Fields
    #
    def test_simple_fields(self):

        class SimpleFieldsSerializer(serializers.Serializer):

            number = serializers.IntegerField()

            is_correct = serializers.BooleanField()

            price = serializers.FloatField()

            choice = serializers.ChoiceField(
                choices=[('AA', 'aaa'), ('BB', 'bbb')])

            name = serializers.CharField(max_length=11)

            data = serializers.DictField(required=False)

            email = serializers.EmailField()

            uri = serializers.URLField(required=False)

            amount = serializers.DecimalField(
                required=False, max_digits=5, decimal_places=3)

            json = serializers.JSONField()

            date_of_birth = serializers.DateField()

            created_at = serializers.DateTimeField()

        expected = {
            'type': 'object',
            'required': [
                'number', 'is_correct', 'price', 'choice', 'name',
                'email', 'json', 'date_of_birth', 'created_at'],
            'properties': {
                'amount': {
                    'type': 'string',
                },
                'number': {
                    'type': 'number',
                },
                'is_correct': {
                    'type': 'boolean',
                },
                'price': {
                    'type': 'number',
                },
                'choice': {
                    'type': 'string',
                    'enum': ['AA', 'BB'],
                },
                'name': {
                    'maxLength': 11,
                    'type': 'string',
                },
                'data': {
                    'type': 'object',
                },
                'email': {
                    'type': 'string',
                    'format': 'email',
                },
                'uri': {
                    'type': 'string',
                    'format': 'uri',
                },
                'json': {
                    'type': 'object',
                },
                'date_of_birth': {
                    'type': 'string',
                    'format': 'date',
                },
                'created_at': {
                    'type': 'string',
                    'format': 'date-time',
                }
            },
        }
        assert to_schema(SimpleFieldsSerializer) == expected

    def test_list_field(self):
        class Serializer(serializers.Serializer):
            numbers = serializers.ListField(
                child=serializers.IntegerField())

            person = serializers.ListField(
                child=PersonSerializer())

        assert to_schema(Serializer) == {
            'type': 'object',
            'required': ['numbers', 'person'],
            'properties': {
                'person': {
                    'items': {
                        'required': ['age'],
                        'type': 'object',
                        'properties': {
                            'name': {
                                'maxLength': 123,
                                'type': 'string'
                            },
                            'age': {
                                'type': 'number',
                                'minimum': 18
                            },
                        },
                    },
                    'type': 'array'
                },
                'numbers': {
                    'items': {
                        'type': 'number'
                    },
                    'type': 'array'
                },
            },
        }

    #
    # Method Derived Serializer Fields
    #
    def test_method_derived_fields(self):

        class MethodDerivedFieldsSerializer(serializers.Serializer):

            number = serializers.SerializerMethodField()

            ingredients = serializers.SerializerMethodField()

            names = serializers.SerializerMethodField()

            hosts = serializers.SerializerMethodField()

            owner = serializers.SerializerMethodField()

            def get_number(self, *args, **kwargs) -> float:
                return 1.45

            def get_ingredients(self, *args, **kwargs) -> [int]:
                return [1, 34]

            def get_names(self, *args, **kwargs) -> [str]:
                return ['Jake', 'John']

            def get_hosts(self, *args, **kwargs) -> [PersonSerializer]:
                return [{'name': 'John', 'age': 24}]

            def get_owner(self, *args, **kwargs) -> PersonSerializer:
                return {'name': 'John', 'age': 24}

        assert to_schema(MethodDerivedFieldsSerializer) == {
            'type': 'object',
            'required': ['number', 'ingredients', 'names', 'hosts', 'owner'],
            'properties': {
                'number': {
                    'type': 'float',
                },
                'ingredients': {
                    'type': 'array',
                    'items': {
                        'type': 'integer',
                    },
                },
                'names': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                },
                'hosts': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'required': ['age'],
                        'properties': {
                            'name': {
                                'type': 'string',
                                'maxLength': 123,
                            },
                            'age': {
                                'type': 'number',
                                'minimum': 18,
                            },
                        },
                    },
                },
                'owner': {
                    'type': 'object',
                    'required': ['age'],
                    'properties': {
                        'name': {
                            'type': 'string',
                            'maxLength': 123,
                        },
                        'age': {
                            'type': 'number',
                            'minimum': 18,
                        },
                    },
                },
            },
        }

    #
    # Nested Serializer
    #
    def test_nested_party_serializer(self):

        assert to_schema(PartySerializer) == {
            'type': 'object',
            'required': ['guests', 'host', 'food'],
            'properties': {
                'host': {
                    'type': 'object',
                    'required': ['name', 'is_underaged'],
                    'properties': {
                        'name': {
                            'type': 'string',
                            'maxLength': 100,
                        },
                        'age': {
                            'type': 'number',
                        },
                        'is_underaged': {
                            'type': 'boolean',
                        },
                        'is_ready': {
                            'type': 'boolean',
                        },
                    },
                },
                'food': {
                    'type': 'object',
                    'required': ['provider', 'amount'],
                    'properties': {
                        'provider': {
                            'type': 'object',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                },
                            },
                        },
                        'amount': {
                            'type': 'number',
                        },
                    },
                },
                'guests': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'required': ['age'],
                        'properties': {
                            'name': {
                                'type': 'string',
                                'maxLength': 123,
                            },
                            'age': {
                                'type': 'number',
                                'minimum': 18,
                            },
                        },
                    },
                },
            },
        }

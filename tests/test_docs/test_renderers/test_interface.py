# -*- coding: utf-8 -*-

from django.test import TestCase
from django.db import models

from lily.base import serializers, parsers
from lily.docs.renderers.interface import InterfaceRenderer


class Human(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    class Meta:
        app_label = 'base'


class HumanQueryParser(parsers.QueryParser):
    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class HumanBodyParser(parsers.BodyParser):
    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class HumanSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)


class HumanModelSerializer(serializers.ModelSerializer):
    is_underaged = serializers.SerializerMethodField()

    class Meta:
        model = Human
        fields = ('name', 'age', 'is_ready', 'is_underaged')

    def get_is_underaged(self, instance) -> bool:
        return instance.age > 18


class ProviderSerializer(serializers.Serializer):
    name = serializers.CharField(default='Johnny')


class FoodSerializer(serializers.Serializer):

    provider = ProviderSerializer()

    amount = serializers.IntegerField()


class PartySerializer(serializers.Serializer):

    guests = HumanSerializer(many=True)

    host = HumanModelSerializer()

    food = FoodSerializer()


class InterfaceRendererTestCase(TestCase):

    #
    # Body Parser
    #
    def test_person_body_parser(self):

        assert InterfaceRenderer(HumanBodyParser).render().serialize() == {
            'interface': {
                'interface': {
                    'age': 'number',
                    'name?': 'string',
                },
                'name': 'RequestBody',
            },
            'enums': {},
        }

    def test_person_query_parser(self):

        assert InterfaceRenderer(HumanQueryParser).render().serialize() == {
            'interface': {
                'interface': {
                    'age': 'number',
                    'name?': 'string',
                },
                'name': 'RequestQuery',
            },
            'enums': {},
        }

    #
    # Serializer
    #
    def test_person_serializer(self):

        assert InterfaceRenderer(HumanSerializer).render().serialize() == {
            'interface': {
                'name': 'Response',
                'interface': {
                    'age': 'number',
                    'name?': 'string',
                }
            },
            'enums': {},
        }

    #
    # Model Serializer
    #
    def test_person_model_serializer(self):

        assert InterfaceRenderer(
            HumanModelSerializer
        ).render().serialize() == {
            'interface': {
                'name': 'Response',
                'interface': {
                    'name': 'string',
                    'age?': 'number',
                    'is_underaged': 'boolean',
                    'is_ready?': 'boolean',
                },
            },
            'enums': {},
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

        assert InterfaceRenderer(
            SimpleFieldsSerializer
        ).render().serialize() == {
            'interface': {
                'name': 'Response',
                'interface': {
                    'number': 'number',
                    'is_correct': 'boolean',
                    'price': 'number',
                    'choice': 'ResponseChoice',
                    'name': 'string',
                    'email': 'string',
                    'json': 'object',
                    'date_of_birth': 'string',
                    'created_at': 'string',
                    'amount?': 'string',
                    'data?': 'object',
                    'uri?': 'string',
                }
            },
            'enums': {
                'ResponseChoice': ['AA', 'BB'],
            },
        }

    def test_list_field(self):
        class Serializer(serializers.Serializer):
            numbers = serializers.ListField(
                child=serializers.IntegerField())

            person = serializers.ListField(
                child=HumanSerializer())

        assert InterfaceRenderer(Serializer).render().serialize() == {
            'interface': {
                'name': 'Response',
                'interface': {
                    'person': {
                        '__type': 'array',
                        '__items': {
                            'name?': 'string',
                            'age': 'number',
                        }
                    },
                    'numbers': {
                        '__type': 'array',
                        '__items': 'number',
                    },
                },
            },
            'enums': {},
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

            def get_hosts(self, *args, **kwargs) -> [HumanSerializer]:
                return [{'name': 'John', 'age': 24}]

            def get_owner(self, *args, **kwargs) -> HumanSerializer:
                return {'name': 'John', 'age': 24}

        assert InterfaceRenderer(
            MethodDerivedFieldsSerializer
        ).render().serialize() == {
            'interface': {
                'name': 'Response',
                'interface': {
                    'number': 'number',
                    'ingredients': {
                        '__type': 'array',
                        '__items': 'number',
                    },
                    'names': {
                        '__type': 'array',
                        '__items': 'string',
                    },
                    'hosts': {
                        '__type': 'array',
                        '__items': {
                            'name?': 'string',
                            'age': 'number',
                        }
                    },
                    'owner': {
                        'name?': 'string',
                        'age': 'number',
                    },
                },
            },
            'enums': {},
        }

    #
    # Nested Serializer
    #
    def test_nested_party_serializer(self):

        assert InterfaceRenderer(PartySerializer).render().serialize() == {
            'interface': {
                'name': 'Response',
                'interface': {
                    'guests': {
                        '__type': 'array',
                        '__items': {
                            'name?': 'string',
                            'age': 'number',
                        }
                    },
                    'host': {
                        'name': 'string',
                        'age?': 'number',
                        'is_underaged': 'boolean',
                        'is_ready?': 'boolean',
                    },
                    'food': {
                        'provider': {
                            'name?': 'string',
                        },
                        'amount': 'number',
                    }
                }
            },
            'enums': {},
        }

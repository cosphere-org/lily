# -*- coding: utf-8 -*-

from django.test import TestCase, override_settings
from django.db import models
import pytest
from mock import Mock, call

from lily.base import serializers, parsers
from docs.renderers.interface import (
    Enum,
    Interface,
    ArrayValue,
    InterfaceRenderer,
    to_camelcase,
)


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

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    #
    # Body Parser
    #
    def test_person_body_parser(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert InterfaceRenderer(HumanBodyParser).render().serialize() == {
            'name': 'RequestBody',
            'uri': 'http://hi.there#123',
            'interface': {
                'age': 'number',
                'name?': 'string',
            },
            'enums': {},
        }

    def test_person_query_parser(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert InterfaceRenderer(HumanQueryParser).render().serialize() == {
            'name': 'RequestQuery',
            'uri': 'http://hi.there#123',
            'interface': {
                'age': 'number',
                'name?': 'string',
            },
            'enums': {},
        }

    #
    # Serializer
    #
    def test_person_serializer(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert InterfaceRenderer(HumanSerializer).render().serialize() == {
            'name': 'Response',
            'uri': 'http://hi.there#123',
            'interface': {
                'age': 'number',
                'name?': 'string',
            },
            'enums': {},
        }

    #
    # Model Serializer
    #
    def test_person_model_serializer(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert InterfaceRenderer(
            HumanModelSerializer
        ).render().serialize() == {
            'name': 'Response',
            'uri': 'http://hi.there#123',
            'interface': {
                'name': 'string',
                'age?': 'number',
                'is_underaged': 'boolean',
                'is_ready?': 'boolean',
            },
            'enums': {},
        }

    #
    # Method Derived Serializer Fields
    #
    def test_simple_fields(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

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
            'name': 'Response',
            'uri': 'http://hi.there#123',
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
            },
            'enums': {
                'ResponseChoice': ['AA', 'BB'],
            },
        }

    def test_list_field(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        class Serializer(serializers.Serializer):
            numbers = serializers.ListField(
                child=serializers.IntegerField())

            person = serializers.ListField(
                child=HumanSerializer())

        assert InterfaceRenderer(Serializer).render().serialize() == {
            'name': 'Response',
            'uri': 'http://hi.there#123',
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
            'enums': {},
        }

    #
    # Method Derived Serializer Fields
    #
    def test_method_derived_fields(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

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
            'name': 'Response',
            'uri': 'http://hi.there#123',
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
            'enums': {},
        }

    #
    # Nested Serializer
    #
    def test_nested_party_serializer(self):

        self.mocker.patch.object(
            Interface, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert InterfaceRenderer(PartySerializer).render().serialize() == {
            'name': 'Response',
            'uri': 'http://hi.there#123',
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
            },
            'enums': {},
        }

    #
    # test_get_repository_uri
    #
    def test_get_repository_uri(self):

        self.mocker.patch(
            'docs.renderers.interface.config',
            Mock(repository='http://repo', last_commit_hash='1234'))

        interface = InterfaceRenderer(HumanSerializer).render()
        interface.meta = {
            'path': '/some/path',
            'first_line': 11,
        }

        assert (
            interface.get_repository_uri() ==
            'http://repo/src/1234/some/path/#lines-11')

    #
    # get_meta
    #
    @override_settings(LILY_PROJECT_BASE='/home/projects/lily')
    def test_get_meta(self):

        getfile = Mock(return_value='/home/projects/lily/a/views.py')
        getsourcelines = Mock(return_value=[None, 11])
        self.mocker.patch(
            'docs.renderers.interface.inspect',
            Mock(getfile=getfile, getsourcelines=getsourcelines))

        renderer = InterfaceRenderer(HumanSerializer)

        assert renderer.get_meta(HumanSerializer) == {
            'first_line': 11,
            'path': '/a/views.py',
        }
        assert getfile.call_args_list == [
            call(HumanSerializer), call(HumanSerializer)]
        assert getsourcelines.call_args_list == [
            call(HumanSerializer), call(HumanSerializer)]

    #
    # remove_enums_duplicates
    #
    def test_remove_enums_duplicates(self):

        interface = InterfaceRenderer(HumanSerializer).render()
        interface.enums = [
            Enum('kind', ['1', '2']),

            # -- duplicated name, same values
            Enum('kind', ['1', '2']),

            # -- duplicated name, same values - different order
            Enum('kind', ['2', '1']),

            # -- duplicated name, different values
            Enum('kind', ['1', '2', '3']),

            # -- other duplicated name, different values
            Enum('kind', ['1', 'a']),
        ]

        enums = interface.remove_enums_duplicates()

        assert len(enums) == 3
        enums_index = {enum.name: enum.values for enum in enums}
        assert enums_index['ResponseKind'] == ['1', '2']
        assert enums_index['ResponseKind1'] == ['1', '2', '3']
        assert enums_index['ResponseKind2'] == ['1', 'a']


def get_interface(raw_interface):

    interface = InterfaceRenderer(HumanSerializer).render()
    interface.interface = raw_interface

    return interface


@pytest.mark.parametrize(
    'raw_interface, expected',
    [
        # -- empty to empty
        ({}, {'enums': {}, 'interface': {}}),

        # -- single value interface
        (
            {
                'name': 'string',
            },
            {
                'enums': {},
                'interface': {
                    'name': 'string',
                },
            }
        ),

        #
        # Nested Enums
        #
        (
            {
                'owner': get_interface({
                    'name': Enum('NameEnum', ['Jack', 'Jake']),
                    'ingredient': get_interface({
                        'type': Enum('TypeEnum', ['RightOne']),
                        'is_ready': 'boolean',
                        'creator': get_interface({
                            'age': Enum('AgeEnum', ['Adult']),
                        }),
                    }),
                }),
            },
            {
                'enums': {},
                'interface': {
                    'owner': {
                        'name': 'NameEnum',
                        'ingredient': {
                            'type': 'TypeEnum',
                            'is_ready': 'boolean',
                            'creator': {
                                'age': 'AgeEnum',
                            }
                        },
                    }
                },
            }
        ),

        #
        # Nested Interfaces
        #
        (
            {
                'owner': get_interface({
                    'name': 'string',
                    'ingredient': get_interface({
                        'type': 'string',
                        'is_ready': 'boolean',
                        'creator': get_interface({
                            'age': 'number',
                        }),
                    }),
                }),
            },
            {
                'enums': {},
                'interface': {
                    'owner': {
                        'name': 'string',
                        'ingredient': {
                            'type': 'string',
                            'is_ready': 'boolean',
                            'creator': {
                                'age': 'number',
                            }
                        },
                    }
                },
            }
        ),

        #
        # ArrayValue
        #

        # -- Interface - ArrayValue
        (
            {
                'owner': ArrayValue(get_interface({
                    'name': 'string',
                    'age': 'number',
                })),
            },
            {
                'enums': {},
                'interface': {
                    'owner': {
                        '__type': 'array',
                        '__items': {
                            'name': 'string',
                            'age': 'number',
                        },
                    }
                },
            }
        ),

        # -- Enum - ArrayValue
        (
            {
                'statuses': ArrayValue(Enum('StatuseEnum', ['ok', 'not_ok'])),
            },
            {
                'enums': {},
                'interface': {
                    'statuses': {
                        '__type': 'array',
                        '__items': 'StatuseEnum',
                    }
                },
            }
        ),

        # -- simple type - ArrayValue
        (
            {
                'choices': ArrayValue('string'),
            },
            {
                'enums': {},
                'interface': {
                    'choices': {
                        '__type': 'array',
                        '__items': 'string',
                    }
                },
            }
        ),
    ])
def test_serialize(raw_interface, expected):

    interface = InterfaceRenderer(HumanSerializer).render()
    interface.interface = raw_interface

    serialized = interface.serialize()
    del serialized['name']
    del serialized['uri']
    assert serialized == expected


@pytest.mark.parametrize(
    'name, expected', [
        # -- empty to empty
        ('', ''),

        # -- single letter capital to same
        ('A', 'A'),

        # -- camel to camel
        ('Abc', 'Abc'),

        # -- camel to camel
        ('Abc', 'Abc'),

        # -- all UPPER to camel
        ('ABCD', 'Abcd'),

        # -- all lower to camel
        ('abcd', 'Abcd'),

        # -- underscore case
        ('ab_cde_f', 'AbCdeF'),

        # -- mixed case
        ('ab_CDe_f', 'AbCdeF'),

    ])
def test_to_camelcase(name, expected):

    assert to_camelcase(name) == expected

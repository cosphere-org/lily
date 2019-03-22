
from unittest.mock import Mock, call

from django.test import TestCase
from django.db import models
import pytest
from lily_assistant.config import Config

from lily.base import serializers, parsers
from lily.base.models import JSONSchemaField, array, string
from lily.entrypoint.renderers.schema import (
    Schema,
    ArrayValue,
    SchemaRenderer,
    MissingSchemaMappingError,
)


class Human(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    pets = JSONSchemaField(schema=array(string()))

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
        fields = ('name', 'age', 'is_ready', 'is_underaged', 'pets')

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


class SchemaRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    #
    # Body Parser
    #
    def test_person_body_parser(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert SchemaRenderer(HumanBodyParser).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                        'minimum': 18,
                    },
                    'name': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
        }

    def test_person_query_parser(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert SchemaRenderer(HumanQueryParser).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                        'minimum': 18,
                    },
                    'name': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
        }

    #
    # Serializer
    #
    def test_person_serializer(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert SchemaRenderer(HumanSerializer).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': ['age'],
                'properties': {
                    'age': {
                        'type': 'integer',
                        'minimum': 18,
                    },
                    'name': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                },
            },
        }

    #
    # Model Serializer
    #
    def test_person_model_serializer(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        assert SchemaRenderer(
            HumanModelSerializer
        ).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'maxLength': 100,
                    },
                    'age': {
                        'minimum': -2147483648,
                        'maximum': 2147483647,
                        'type': 'integer',
                    },
                    'is_underaged': {
                        'type': 'boolean',
                    },
                    'is_ready': {
                        'type': 'boolean',
                    },
                    'pets': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                },
                'required': ['name', 'is_ready', 'is_underaged', 'pets'],
            },
        }

    #
    # Method Derived Serializer Fields
    #
    def test_simple_fields(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
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

        assert SchemaRenderer(
            SimpleFieldsSerializer
        ).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': [
                    'number', 'is_correct', 'price', 'choice', 'name',
                    'email', 'json', 'date_of_birth', 'created_at'],
                'properties': {
                    'amount': {
                        'type': 'string',
                    },
                    'number': {
                        'type': 'integer',
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
                        'type': 'any',
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
        }

    def test_list_field(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        class Serializer(serializers.Serializer):
            numbers = serializers.ListField(
                child=serializers.IntegerField())

            person = serializers.ListField(
                child=HumanSerializer())

            # -- optional list fields
            ids = serializers.ListField(
                child=serializers.IntegerField(), required=False)

            providers = serializers.ListField(
                child=ProviderSerializer(), required=False)

        assert SchemaRenderer(Serializer).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': ['numbers', 'person'],
                'properties': {
                    'person': {
                        'type': 'array',
                        'items': {
                            'required': ['age'],
                            'type': 'object',
                            'properties': {
                                'name': {
                                    'maxLength': 123,
                                    'type': 'string'
                                },
                                'age': {
                                    'type': 'integer',
                                    'minimum': 18
                                },
                            },
                        },
                    },
                    'numbers': {
                        'type': 'array',
                        'items': {
                            'type': 'integer'
                        },
                    },
                    'ids': {
                        'type': 'array',
                        'items': {
                            'type': 'integer'
                        },
                    },
                    'providers': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                }
                            },
                            'required': [],
                        },
                    },
                },
            },
        }

    #
    # Method Derived Serializer Fields
    #
    def test_method_derived_fields(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
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

        assert SchemaRenderer(
            MethodDerivedFieldsSerializer
        ).render().serialize() == {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': [
                    'number', 'ingredients', 'names', 'hosts', 'owner'],
                'properties': {
                    'number': {
                        'type': 'number',
                    },
                    'ingredients': {
                        'type': 'array',
                        'items': {
                            'type': 'number',
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
                                    'type': 'integer',
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
                                'type': 'integer',
                                'minimum': 18,
                            },
                        },
                    },
                },
            },
        }

    #
    # Nested Serializer
    #
    def test_nested_party_serializer(self):

        self.mocker.patch.object(
            Schema, 'get_repository_uri'
        ).return_value = 'http://hi.there#123'

        expected = {
            'uri': 'http://hi.there#123',
            'schema': {
                'type': 'object',
                'required': ['guests', 'host', 'food'],
                'properties': {
                    'host': {
                        'type': 'object',
                        'required': [
                            'name',
                            'is_ready',
                            'is_underaged',
                            'pets',
                        ],
                        'properties': {
                            'name': {
                                'type': 'string',
                                'maxLength': 100,
                            },
                            'age': {
                                'type': 'integer',
                                'minimum': -2147483648,
                                'maximum': 2147483647
                            },
                            'is_underaged': {
                                'type': 'boolean',
                            },
                            'is_ready': {
                                'type': 'boolean',
                            },
                            'pets': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            }
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
                                'required': [],
                            },
                            'amount': {
                                'type': 'integer',
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
                                    'type': 'integer',
                                    'minimum': 18,
                                },
                            },
                        },
                    },
                },
            },
        }

        assert SchemaRenderer(
            PartySerializer).render().serialize() == expected

    def test_missing_mapping(self):

        class UnknownField:
            pass

        class Serializer:

            def get_fields(self):
                return {'name': UnknownField()}

        with pytest.raises(MissingSchemaMappingError):
            SchemaRenderer(Serializer).render().serialize()

    #
    # test_get_repository_uri
    #
    def test_get_repository_uri__bitbucket(self):

        class MockConfig:

            repository = 'http://bitbucket.com'

            last_commit_hash = '1234'

            @classmethod
            def get_project_path(cls):
                return '/home/projects/lily'

        self.mocker.patch(
            'lily.entrypoint.renderers.schema.Config', MockConfig)

        schema = SchemaRenderer(HumanSerializer).render()
        schema.meta = {
            'path': '/some/path',
            'first_line': 11,
        }

        assert (
            schema.get_repository_uri() ==
            'http://bitbucket.com/src/1234/some/path/#lines-11')

    def test_get_repository_uri__github(self):

        class MockConfig:

            repository = 'http://github.com/what'

            last_commit_hash = '1234'

            @classmethod
            def get_project_path(cls):
                return '/home/projects/lily'

        self.mocker.patch(
            'lily.entrypoint.renderers.schema.Config', MockConfig)

        schema = SchemaRenderer(HumanSerializer).render()
        schema.meta = {
            'path': '/some/path',
            'first_line': 11,
        }

        assert (
            schema.get_repository_uri() ==
            'http://github.com/what/blob/1234/some/path/#L11')

    #
    # get_meta
    #
    def test_get_meta(self):

        self.mocker.patch.object(
            Config, 'get_project_path').return_value = '/home/projects/lily'
        getfile = Mock(return_value='/home/projects/lily/a/views.py')
        getsourcelines = Mock(return_value=[None, 11])
        self.mocker.patch(
            'lily.entrypoint.renderers.schema.inspect',
            Mock(getfile=getfile, getsourcelines=getsourcelines))

        renderer = SchemaRenderer(HumanSerializer)

        assert renderer.get_meta(HumanSerializer) == {
            'first_line': 11,
            'path': '/a/views.py',
        }
        assert getfile.call_args_list == [
            call(HumanSerializer), call(HumanSerializer)]
        assert getsourcelines.call_args_list == [
            call(HumanSerializer), call(HumanSerializer)]


def get_schema(raw_schema):

    schema = SchemaRenderer(HumanSerializer).render()
    schema.schema = raw_schema

    return schema


@pytest.mark.parametrize(
    'raw_schema, expected',
    [
        # -- empty to empty
        (
            {
                'type': 'object',
                'properties': {},
                'required': [],
            },
            {'schema': {}},
        ),

        # -- single value schema
        (
            {
                'type': 'object',
                'properties': {
                    'name': 'string',
                },
                'required': ['name'],
            },
            {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'name': 'string',
                    },
                    'required': ['name'],
                },
            }
        ),

        #
        # Nested Schemas
        #
        (
            {
                'type': 'object',
                'required': ['owner'],
                'properties': {
                    'owner': get_schema({
                        'type': 'object',
                        'properties': {
                            'name': 'string',
                            'ingredient': get_schema({
                                'type': 'object',
                                'required': ['is_ready', 'name'],
                                'properties': {
                                    'name': 'string',
                                    'is_ready': 'boolean',
                                    'creator': get_schema({
                                        'type': 'object',
                                        'required': [],
                                        'properties': {
                                            'age': 'number',
                                        },
                                    }),
                                },
                            }),
                        },
                        'required': ['name'],
                    }),
                },
            },
            {
                'schema': {
                    'type': 'object',
                    'required': ['owner'],
                    'properties': {
                        'owner': {
                            'type': 'object',
                            'properties': {
                                'name': 'string',
                                'ingredient': {
                                    'type': 'object',
                                    'required': ['is_ready', 'name'],
                                    'properties': {
                                        'name': 'string',
                                        'is_ready': 'boolean',
                                        'creator': {
                                            'type': 'object',
                                            'required': [],
                                            'properties': {
                                                'age': 'number',
                                            },
                                        },
                                    },
                                },
                            },
                            'required': ['name'],
                        },
                    },
                },
            }
        ),

        #
        # ArrayValue
        #

        # -- Schema - ArrayValue
        (
            {
                'type': 'object',
                'required': ['owner'],
                'properties': {
                    'owner': ArrayValue(get_schema({
                        'type': 'object',
                        'required': [],
                        'properties': {
                            'name': 'string',
                            'age': 'number',
                        },
                    })),
                },
            },
            {
                'schema': {
                    'type': 'object',
                    'required': ['owner'],
                    'properties': {
                        'owner': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': [],
                                'properties': {
                                    'name': 'string',
                                    'age': 'number',
                                },
                            },
                        },
                    },
                },
            }
        ),

        # -- simple type - ArrayValue
        (
            {
                'type': 'object',
                'required': ['choices'],
                'properties': {
                    'choices': ArrayValue('string'),
                }
            },
            {
                'schema': {
                    'type': 'object',
                    'required': ['choices'],
                    'properties': {
                        'choices': {
                            'type': 'array',
                            'items': 'string',
                        },
                    }
                },
            }
        ),
    ])
def test_serialize(raw_schema, expected, mocker):

    mocker.patch.object(
        Schema, 'get_repository_uri').return_value = 'uri'

    schema = SchemaRenderer(HumanSerializer).render()
    schema.schema = raw_schema

    serialized = schema.serialize()
    del serialized['uri']
    assert serialized == expected

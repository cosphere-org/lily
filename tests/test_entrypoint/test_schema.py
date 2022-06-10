
from unittest.mock import Mock, call
from enum import Enum

from django.test import TestCase
from django.db import models
import pytest

from lily.base.models import EnumChoiceField
from lily.base import serializers, parsers
from lily.base.models import (
    array,
    const,
    JSONSchemaField,
    multischema,
    number,
    object,
    one_of,
    string,
    enum,
)
from lily.entrypoint.schema import (
    Schema,
    ArrayValue,
    SchemaRenderer,
    MissingSchemaMappingError,
    ForbiddenFieldError,
)


class Enumer(models.Model):

    nickname = EnumChoiceField(
        max_length=100,
        enum_name='human_nicknames',
        choices=[('Jack', 'Jack'), ('Abel', 'Abel')])

    class Brands(Enum):
        nice = 'nice'

        awesome = 'awesome'

    brand = EnumChoiceField(max_length=100, enum=Brands)

    class Meta:
        app_label = 'base'


class ForbiddenSerializer(serializers.Serializer):

    _type = 'forbidden'

    picks = serializers.ChoiceField(choices=('A', 'B'))


class Human(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    pets = JSONSchemaField(schema=array(string()))

    class Meta:
        app_label = 'base'


class JSONSchemaSerializer(serializers.Serializer):

    _type = 'json'

    names = serializers.JSONSchemaField(schema=array(string()))

    users = serializers.SerializerMethodField()

    owners = serializers.SerializerMethodField()

    class Shopping(Enum):
        bread = 'bread'

        milk = 'milk'

    shoppings = serializers.JSONSchemaField(
        schema=array(
            object(type=enum(Shopping))))

    selected_shoppings = serializers.JSONSchemaField(
        schema=one_of(
            object(type=enum(Shopping, const=Shopping.bread.value)),
            object(type=enum(Shopping, const=Shopping.milk.value))))

    def get_users(self, instance) -> [object(name=const('YO'), age=number())]:  # noqa
        return instance['users']

    def get_owners(self, instance) -> array(object(name=string(), age=number())):  # noqa
        return instance['owners']


class JSONSchemaMultiSchemaModel(models.Model):

    entity = JSONSchemaField(schema=multischema(
        {
            'PERSON': object(
                type=const('PERSON'),
                name=string(),
                required=['type', 'name']),
            'ANIMAL': object(
                type=const('ANIMAL'),
                age=number(),
                required=['type', 'age'])
        },
        by_field='type'))

    class Meta:
        app_label = 'base'


class JSONSchemaMultiSchemaSerializer(serializers.ModelSerializer):

    _type = 'json_multischema'

    class Meta:
        model = JSONSchemaMultiSchemaModel
        fields = ('entity',)


class HumanQueryParser(parsers.Parser):

    name = parsers.CharField(max_length=123, required=False)

    age = parsers.IntegerField(min_value=18)


class HumanBodyParser(parsers.Parser):

    name = parsers.CharField(max_length=123, required=False)

    age = parsers.IntegerField(min_value=18)


class HumanSerializer(serializers.Serializer):

    _type = 'human'

    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)

    place = serializers.EnumChoiceField(choices=[0, 1, 2], enum_name='place')


class CycleJSONSerializer(serializers.Serializer):

    _type = 'cycle'

    local_id = serializers.IntegerField(allow_null=True)

    stage_id = serializers.IntegerField(allow_null=True)

    entity = serializers.JSONField()


class CyclesJSONSerializer(serializers.Serializer):

    _type = 'cycles'

    card_cycle = serializers.SerializerMethodField()

    path_cycle = serializers.SerializerMethodField()

    def get_card_cycle(self, instance) -> [CycleJSONSerializer]:
        return []

    def get_path_cycle(self, instance) -> [CycleJSONSerializer]:
        return []


class HumanModelSerializer(serializers.ModelSerializer):

    _type = 'human'

    is_underaged = serializers.SerializerMethodField()

    class Meta:
        model = Human
        fields = (
            'name', 'age', 'is_ready', 'is_underaged', 'pets')

    def get_is_underaged(self, instance) -> bool:
        return instance.age > 18


class EnumerModelSerializer(serializers.ModelSerializer):

    _type = 'enumer'

    class Meta:
        model = Enumer
        fields = ('nickname', 'brand')


class ProviderSerializer(serializers.Serializer):

    _type = 'provider'

    name = serializers.CharField(default='Johnny')


class FoodSerializer(serializers.Serializer):

    _type = 'food'

    provider = ProviderSerializer()

    amount = serializers.IntegerField()


class PartySerializer(serializers.Serializer):

    _type = 'party'

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

        assert SchemaRenderer(
            HumanBodyParser,
            parser_type=parsers.ParserTypeEnum.BODY.value
        ).render().serialize() == {
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

        assert SchemaRenderer(
            HumanQueryParser,
            parser_type=parsers.ParserTypeEnum.QUERY.value
        ).render().serialize() == {
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

        assert SchemaRenderer(HumanSerializer).render().serialize() == {
            'schema': {
                'type': 'object',
                'required': ['age', 'place'],
                'entity_type': 'human',
                'properties': {
                    'age': {
                        'type': 'integer',
                        'minimum': 18,
                    },
                    'name': {
                        'maxLength': 123,
                        'type': 'string',
                    },
                    'place': {
                        'enum': [0, 1, 2],
                        'enum_name': 'place',
                        'type': 'integer',
                    },
                },
            },
        }

    def test_object_json_serializer(self):

        assert SchemaRenderer(CycleJSONSerializer).render().serialize() == {
            'schema': {
                'type': 'object',
                'entity_type': 'cycle',
                'properties': {
                    'local_id': {'type': 'integer'},
                    'stage_id': {'type': 'integer'},
                    'entity': {'type': 'any'},
                },
                'required': ['entity', 'local_id', 'stage_id'],
            },
        }

    def test_array_json_serializer(self):

        rendered = SchemaRenderer(CyclesJSONSerializer).render().serialize()

        assert rendered == {
            'schema': {
                'type': 'object',
                'entity_type': 'cycles',
                'properties': {
                    'card_cycle': {
                        'type': 'array',
                        'items': {
                            'entity_type': 'cycle',
                            'type': 'object',
                            'properties': {
                                'entity': {'type': 'any'},
                                'local_id': {'type': 'integer'},
                                'stage_id': {'type': 'integer'},
                            },
                            'required': ['entity', 'local_id', 'stage_id'],
                        },
                    },
                    'path_cycle': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'entity_type': 'cycle',
                            'properties': {
                                'entity': {'type': 'any'},
                                'local_id': {'type': 'integer'},
                                'stage_id': {'type': 'integer'},
                            },
                            'required': ['entity', 'local_id', 'stage_id'],
                        },
                    },
                },
                'required': ['card_cycle', 'path_cycle'],
            },
        }

    def test_method_json_serializer(self):

        expected = {
            'schema': {
                'type': 'object',
                'entity_type': 'json',
                'properties': {
                    'names': {
                        'type': 'array',
                        'items': {'type': 'string'},
                    },
                    'owners': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'age': {'type': 'number'},
                                'name': {'type': 'string'},
                            },
                        },
                    },
                    'users': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'age': {'type': 'number'},
                                'name': {
                                    'type': 'string',
                                    'pattern': '^YO$',
                                    'const': 'YO',
                                },
                            },
                        },
                    },
                    'selected_shoppings': {
                        'by_field': None,
                        'oneOf': [
                            {
                                'type': 'object',
                                'properties': {
                                    'type': {
                                        'const_value': 'bread',
                                        'enum': ['bread', 'milk'],
                                        'enum_name': 'Shopping',
                                        'type': 'string'
                                    }
                                },
                            },
                            {
                                'type': 'object',
                                'properties': {
                                    'type': {
                                        'const_value': 'milk',
                                        'enum': ['bread', 'milk'],
                                        'enum_name': 'Shopping',
                                        'type': 'string'
                                    }
                                },
                            },
                        ],
                    },
                    'shoppings': {
                        'type': 'array',
                        'items': {
                            'properties': {
                                'type': {
                                    'enum': ['bread', 'milk'],
                                    'enum_name': 'Shopping',
                                    'type': 'string'
                                }
                            },
                            'type': 'object'
                        },
                    },

                },
                'required': [
                    'names',
                    'owners',
                    'selected_shoppings',
                    'shoppings',
                    'users',
                ],
            },
        }
        rendered = SchemaRenderer(JSONSchemaSerializer).render().serialize()

        assert rendered == expected

    def test_method_json_multischema_serializer(self):

        assert SchemaRenderer(
            JSONSchemaMultiSchemaSerializer
        ).render().serialize() == {
            'schema': {
                'type': 'object',
                'required': ['entity'],
                'properties': {
                    'entity': {
                        'oneOf': [
                            {
                                'type': 'object',
                                'properties': {
                                    'type': {
                                        'type': 'string',
                                        'const': 'PERSON',
                                        'pattern': '^PERSON$'
                                    },
                                    'name': {
                                        'type': 'string'
                                    }
                                },
                                'required': ['type', 'name']
                            },
                            {
                                'type': 'object',
                                'properties': {
                                    'type': {
                                        'type': 'string',
                                        'const': 'ANIMAL',
                                        'pattern': '^ANIMAL$'
                                    },
                                    'age': {
                                        'type': 'number'
                                    }
                                },
                                'required': ['type', 'age']
                            }
                        ]
                    }
                },
                'entity_type': 'json_multischema',
            }
        }

    #
    # Model Serializer
    #
    def test_person_model_serializer(self):

        rendered = SchemaRenderer(
            HumanModelSerializer
        ).render().serialize()

        assert rendered == {
            'schema': {
                'type': 'object',
                'entity_type': 'human',
                'properties': {
                    'name': {
                        'type': 'string',
                        'maxLength': 100,
                    },
                    'age': {
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
                'required': ['is_underaged', 'name', 'is_ready', 'pets'],
            },
        }

    def test_enumer_model_serializer(self):

        rendered = SchemaRenderer(
            EnumerModelSerializer
        ).render().serialize()

        assert rendered == {
            'schema': {
                'entity_type': 'enumer',
                'properties': {
                    'brand': {
                        'enum': ['awesome', 'nice'],
                        'enum_name': 'Brands',
                        'type': 'string'
                    },
                    'nickname': {
                        'enum': ['Abel', 'Jack'],
                        'enum_name': 'human_nicknames',
                        'type': 'string',
                    },
                },
                'required': ['nickname', 'brand'],
                'type': 'object',
            },
        }

    def test_forbidden_serializer(self):

        with pytest.raises(ForbiddenFieldError) as e:
            SchemaRenderer(ForbiddenSerializer).render().serialize()

        assert e.value.args == (
            'picks uses ChoiceField which is forbidden since it leads to '
            'ambiguous client side Enums. Please use `EnumChoiceField` '
            'instead',)

    #
    # Method Derived Serializer Fields
    #
    def test_simple_fields(self):

        class SimpleFieldsSerializer(serializers.Serializer):

            number = serializers.IntegerField()

            is_correct = serializers.BooleanField()

            price = serializers.FloatField()

            choice = serializers.EnumChoiceField(
                enum_name='choice',
                choices=[('AA', 'aaa'), ('BB', 'bbb')])

            name = serializers.CharField(max_length=11)

            whatever = serializers.DictField(required=False)

            email = serializers.EmailField()

            uri = serializers.URLField(required=False)

            amount = serializers.DecimalField(
                required=False, max_digits=5, decimal_places=3)

            json = serializers.JSONField()

            date_of_birth = serializers.DateField()

            created_at = serializers.DateTimeField()

        expected = {
            'schema': {
                'type': 'object',
                'required': [
                    "choice",
                    "created_at",
                    "date_of_birth",
                    "email",
                    "is_correct",
                    "json",
                    "name",
                    "number",
                    "price"
                ],
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
                        'enum_name': 'choice',
                    },
                    'name': {
                        'maxLength': 11,
                        'type': 'string',
                    },
                    'whatever': {
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
        rendered = SchemaRenderer(SimpleFieldsSerializer).render().serialize()

        assert rendered == expected

    def test_list_field(self):

        class Serializer(serializers.Serializer):

            _type = 'complex'

            numbers = serializers.ListField(
                child=serializers.IntegerField())

            person = serializers.ListField(
                child=HumanSerializer())

            # -- optional list fields
            ids = serializers.ListField(
                child=serializers.IntegerField(), required=False)

            providers = serializers.ListField(
                child=ProviderSerializer(), required=False)

        rendered = SchemaRenderer(Serializer).render().serialize()

        assert rendered == {
            'schema': {
                'type': 'object',
                'entity_type': 'complex',
                'required': ['numbers', 'person'],
                'properties': {
                    'person': {
                        'type': 'array',
                        'items': {
                            'required': ['age', 'place'],
                            'type': 'object',
                            'entity_type': 'human',
                            'properties': {
                                'name': {
                                    'maxLength': 123,
                                    'type': 'string'
                                },
                                'age': {
                                    'type': 'integer',
                                    'minimum': 18
                                },
                                'place': {
                                    'enum': [0, 1, 2],
                                    'enum_name': 'place',
                                    'type': 'integer',
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
                            'entity_type': 'provider',
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

        class MethodDerivedFieldsSerializer(serializers.Serializer):

            _type = 'method'

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
            'schema': {
                'type': 'object',
                'required': [
                    'hosts', 'ingredients', 'names', 'number', 'owner'],
                'entity_type': 'method',
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
                            'required': ['age', 'place'],
                            'entity_type': 'human',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'maxLength': 123,
                                },
                                'age': {
                                    'type': 'integer',
                                    'minimum': 18,
                                },
                                'place': {
                                    'enum': [0, 1, 2],
                                    'enum_name': 'place',
                                    'type': 'integer',
                                },
                            },
                        },
                    },
                    'owner': {
                        'type': 'object',
                        'entity_type': 'human',
                        'required': ['age', 'place'],
                        'properties': {
                            'name': {
                                'type': 'string',
                                'maxLength': 123,
                            },
                            'age': {
                                'type': 'integer',
                                'minimum': 18,
                            },
                            'place': {
                                'enum': [0, 1, 2],
                                'enum_name': 'place',
                                'type': 'integer',
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

        expected = {
            'schema': {
                'type': 'object',
                'required': ['food', 'guests', 'host'],
                'entity_type': 'party',
                'properties': {
                    'host': {
                        'type': 'object',
                        'required': [
                            'is_underaged',
                            'name',
                            'is_ready',
                            'pets',
                        ],
                        'entity_type': 'human',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'maxLength': 100,
                            },
                            'age': {
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
                            }
                        },
                    },
                    'food': {
                        'type': 'object',
                        'entity_type': 'food',
                        'required': ['amount', 'provider'],
                        'properties': {
                            'provider': {
                                'type': 'object',
                                'entity_type': 'provider',
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
                            'entity_type': 'human',
                            'required': ['age', 'place'],
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'maxLength': 123,
                                },
                                'age': {
                                    'type': 'integer',
                                    'minimum': 18,
                                },
                                'place': {
                                    'enum': [0, 1, 2],
                                    'enum_name': 'place',
                                    'type': 'integer',
                                },
                            },
                        },
                    },
                },
            },
        }
        rendered = SchemaRenderer(PartySerializer).render().serialize()

        assert rendered == expected

    def test_missing_mapping(self):

        class UnknownField:
            pass

        class Serializer:

            def get_fields(self):
                return {'name': UnknownField()}

        with pytest.raises(MissingSchemaMappingError):
            SchemaRenderer(Serializer).render().serialize()

    #
    # get_meta
    #
    def test_get_meta(self):

        getfile = Mock(return_value='/home/projects/lily/a/views.py')
        getsourcelines = Mock(return_value=[None, 11])
        self.mocker.patch(
            'lily.entrypoint.schema.inspect',
            Mock(getfile=getfile, getsourcelines=getsourcelines))

        renderer = SchemaRenderer(HumanSerializer)

        assert renderer.get_meta(HumanSerializer) == {
            'first_line': 11,
            'path': '/home/projects/lily/a/views.py',
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

    schema = SchemaRenderer(HumanSerializer).render()
    schema.schema = raw_schema

    serialized = schema.serialize()
    assert serialized == expected

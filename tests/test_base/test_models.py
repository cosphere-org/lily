
from enum import Enum

from django.test import TestCase
from django.db import models
from django.db.utils import DataError
from django_fake_model import models as fake_models
from django.core.exceptions import ValidationError
import pytest

from lily.base.models import (
    ImmutableModel,
    JSONSchemaField,
    ValidatingModel,
    EnumChoiceField,
    enum,
    array,
    object,
    string,
)


class SchemaHelpersTestCase(TestCase):

    #
    # ENUM
    #
    def test_enum__from_list(self):

        assert enum('Jack', 'Alice') == {
            'enum': ['Jack', 'Alice'],
            'enum_name': None,
            'type': 'string',
        }
        assert enum(1, 11) == {
            'enum': [1, 11],
            'enum_name': None,
            'type': 'integer',
        }

    def test_enum__from_enum(self):

        class Names(Enum):
            JACK = 'Jack'

            ALICE = 'Alice'

        assert enum(Names) == {
            'enum': ['Jack', 'Alice'],
            'enum_name': 'Names',
            'type': 'string',
        }

        class Ages(Enum):
            kid = 10

            adult = 21

        assert enum(Ages) == {
            'enum': [10, 21],
            'enum_name': 'Ages',
            'type': 'integer',
        }


class ImmutableEntity(fake_models.FakeModel, ImmutableModel):

    name = models.CharField(max_length=10)


@ImmutableEntity.fake_me
class ImmutableModelTestCase(TestCase):

    def test_save_not_allowed_for_existing_instance(self):

        e = ImmutableEntity(name='john')
        e.save()

        with pytest.raises(ImmutableModel.ModelIsImmutableError):
            e.name = 'mark'
            e.save()

    def test_create_allowed(self):

        e = ImmutableEntity.objects.create(name='john')

        assert e.name == 'john'

    def test_validates_on_save(self):

        with pytest.raises(ValidationError) as e:
            ImmutableEntity(name=11 * 'a').save()

        assert e.value.message_dict == {
            'name': [
                'Ensure this value has at most 10 characters (it has 11).',
            ],
        }


class JSONModel(fake_models.FakeModel):

    SCHEMA = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'array',
        'minItems': 1,
        'items': {
            'type': 'object',
            'properties': {
                'answer': {
                    'type': 'string',
                },
                'correct': {
                    'type': 'boolean',
                },
            },
            'required': ['answer', 'correct'],
        },
    }

    answers = JSONSchemaField(schema=SCHEMA)


@JSONModel.fake_me
class JSONSchemaFieldTestCase(TestCase):

    def test_valid_model(self):

        m = JSONModel(answers=[
            {'answer': 'hello', 'correct': True},
        ])
        m.save()

        assert m.answers == [
            {'answer': 'hello', 'correct': True},
        ]

    def test_invalid_model__empty_array(self):

        with pytest.raises(ValidationError) as e:
            JSONModel(answers=[]).clean_fields()

        error = e.value.error_dict['answers'][0]
        assert error.message == 'This field cannot be blank.'

    def test_invalid_model__not_array(self):

        with pytest.raises(ValidationError) as e:
            JSONModel(answers={'hi': 'there'}).clean_fields()

        error = e.value.error_dict['answers'][0]
        assert error.message == (
            "JSON did not validate. PATH: '.' REASON: {'hi': 'there'} "
            "is not of type 'array'"
        )

    def test_invalid_model__invalid_items__wrong_fields(self):

        with pytest.raises(ValidationError) as e:
            JSONModel(answers=[
                {'answer': 'hi', 'correct': True},
                {'NOT_answer': 'hi', 'WHAT_correct': True},
            ]).clean_fields()

        error = e.value.error_dict['answers'][0]
        assert error.message == (
            "JSON did not validate. "
            "PATH: '1' REASON: 'answer' is a required property"
        )


class EnumModel(fake_models.FakeModel):

    answer = EnumChoiceField(
        enum_name='super_enum',
        max_length=8,
        choices=[('A', 'A'), ('B', 'B')])

    class Names(Enum):

        ALICE = 'ALICE'

        JACK = 'JACK'

    name = EnumChoiceField(enum=Names, max_length=8)


@EnumModel.fake_me
class EnumChoiceFieldTestCase(TestCase):

    def test_model(self):

        m = EnumModel(answer='A', name='JACK')
        m.save()

        assert m.answer == 'A'
        assert m.name == 'JACK'

    def test_extra_field_attributes(self):

        for field in EnumModel._meta.fields:
            if field.name == 'answer':
                assert field.enum_name == 'super_enum'

            if field.name == 'name':
                assert field.enum_name == 'Names'
                assert field.choices == [('ALICE', 'ALICE'), ('JACK', 'JACK')]


class ValidatingEntity(fake_models.FakeModel, ValidatingModel):

    name = models.CharField(max_length=10)


class ValidatingEntityWithJSON(fake_models.FakeModel, ValidatingModel):

    tasks = JSONSchemaField(
        schema=array(
            object(
                name=string())))

    def clean(self):
        if len(set([t['name'] for t in self.tasks])) < 2:
            raise ValidationError('at least 2 unique task needed')


@ValidatingEntity.fake_me
@ValidatingEntityWithJSON.fake_me
class ValidatingModelTestCase(TestCase):

    #
    # ValidatingEntity
    #
    def test_validates_on_save(self):

        with pytest.raises(ValidationError) as e:
            ValidatingEntity(name=11 * 'a').save()

        assert e.value.message_dict == {
            'name': [
                'Ensure this value has at most 10 characters (it has 11).',
            ],
        }

    def test_validates_on_create(self):

        with pytest.raises(ValidationError) as e:
            ValidatingEntity.objects.create(name=11 * 'a')

        assert e.value.message_dict == {
            'name': [
                'Ensure this value has at most 10 characters (it has 11).',
            ],
        }

    def test_validates_on_bulk_create(self):

        with pytest.raises(DataError):
            ValidatingEntity.objects.bulk_create([
                ValidatingEntity(name=11 * 'a'),
            ])

    #
    # ValidatingEntityWithJSON
    #
    def test_schema_validation__run_before_clean(self):

        with pytest.raises(ValidationError) as e:
            ValidatingEntityWithJSON.objects.create(tasks={'what': 'hey'})

        assert e.value.message_dict == {
            'tasks': [
                "JSON did not validate. PATH: '.' REASON: {'what': 'hey'} "
                "is not of type 'array'",
            ],
        }

    def test_schema_validation_when_ok_clean_is_called(self):

        with pytest.raises(ValidationError) as e:
            ValidatingEntityWithJSON.objects.create(tasks=[{'name': 'hey'}])

        assert e.value.message_dict == {
            '__all__': ['at least 2 unique task needed'],
        }

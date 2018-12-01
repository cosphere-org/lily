
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
)


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

        try:
            ImmutableEntity(name=11 * 'a').save()

        except ValidationError as e:
            assert e.message_dict == {
                'name': [
                    'Ensure this value has at most 10 characters (it has 11).',
                ],
            }

        else:
            raise AssertionError('should raise exception')


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

        try:
            JSONModel(answers=[]).clean_fields()

        except ValidationError as e:
            error = e.error_dict['answers'][0]
            assert error.message == 'This field cannot be blank.'

        else:
            raise AssertionError('should raise error')

    def test_invalid_model__not_array(self):

        try:
            JSONModel(answers={'hi': 'there'}).clean_fields()

        except ValidationError as e:
            error = e.error_dict['answers'][0]
            assert error.message == (
                "JSON did not validate. PATH: '.' REASON: {'hi': 'there'} "
                "is not of type 'array'"
            )

        else:
            raise AssertionError('should raise error')

    def test_invalid_model__invalid_items__wrong_fields(self):

        try:
            JSONModel(answers=[
                {'answer': 'hi', 'correct': True},
                {'NOT_answer': 'hi', 'WHAT_correct': True},
            ]).clean_fields()

        except ValidationError as e:
            error = e.error_dict['answers'][0]
            assert error.message == (
                "JSON did not validate. "
                "PATH: '1' REASON: 'answer' is a required property"
            )

        else:
            raise AssertionError('should raise error')


class ValidatingEntity(fake_models.FakeModel, ValidatingModel):

    name = models.CharField(max_length=10)


@ValidatingEntity.fake_me
class ValidatingModelTestCase(TestCase):

    def test_validates_on_save(self):

        try:
            ValidatingEntity(name=11 * 'a').save()

        except ValidationError as e:
            assert e.message_dict == {
                'name': [
                    'Ensure this value has at most 10 characters (it has 11).',
                ],
            }

        else:
            raise AssertionError('should raise exception')

    def test_validates_on_create(self):

        try:
            ValidatingEntity.objects.create(name=11 * 'a')

        except ValidationError as e:
            assert e.message_dict == {
                'name': [
                    'Ensure this value has at most 10 characters (it has 11).',
                ],
            }

        else:
            raise AssertionError('should raise exception')

    def test_validates_on_bulk_create(self):

        try:
            ValidatingEntity.objects.bulk_create([
                ValidatingEntity(name=11 * 'a'),
            ])

        except DataError:
            pass

        else:
            raise AssertionError('should raise exception')

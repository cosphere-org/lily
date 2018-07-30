# -*- coding: utf-8 -*-

from django.test import TestCase
from django.db import models
from django_fake_model import models as fake_models
from django.core.exceptions import ValidationError
import pytest

from lily.base.models import ImmutableModel, JSONSchemaField


class ImmutableEntity(fake_models.FakeModel, ImmutableModel):

    name = models.CharField(max_length=100)


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

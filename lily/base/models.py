# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.expressions import RawSQL
from django.contrib.postgres.fields import JSONField
from jsonschema import (
    validate as json_validate,
    ValidationError as JsonValidationError,
)
from django.core.exceptions import ValidationError


class ImmutableModel(models.Model):

    class ModelIsImmutableError(Exception):
        pass

    def save(self, *args, **kwargs):

        if self.id is not None:
            raise ImmutableModel.ModelIsImmutableError(
                '{} model is declared as immutable'.format(
                    self.__class__.__name__))

        super(ImmutableModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class ExtraColumn(RawSQL):

    def __init__(self, sql, params, output_field=None):

        super(ExtraColumn, self).__init__(
            sql, params, output_field=output_field)

    def get_group_by_cols(self):
        return []


class JSONSchemaValidator:

    def __init__(self, schema):
        self.schema = schema

    def __call__(self, value):
        try:
            json_validate(value, self.schema)

        except JsonValidationError as e:
            path = '.'.join([str(p) for p in e.path]) or '.'
            raise ValidationError(
                f"JSON did not validate. PATH: '{path}' REASON: {e.message}"
            )


class JSONSchemaField(JSONField):
    def __init__(self, *args, **kwargs):
        schema = kwargs.pop('schema')

        super(JSONSchemaField, self).__init__(*args, **kwargs)

        self.validators.append(JSONSchemaValidator(schema=schema))

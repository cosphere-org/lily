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


class JSONSchemaField(JSONField):

    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop('schema', {})
        super(JSONSchemaField, self).__init__(*args, **kwargs)

    def clean(self, value, instance):

        try:
            json_validate(value, self.schema)

        except JsonValidationError as e:
            raise ValidationError(e)

        return super(JSONSchemaField, self).clean(value, instance)


import math
from enum import EnumMeta

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
        self.full_clean()

        if self.id is not None:
            raise ImmutableModel.ModelIsImmutableError(
                '{} model is declared as immutable'.format(
                    self.__class__.__name__))

        super(ImmutableModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class ValidatingModel(models.Model):

    def save(self, *args, **kwargs):

        # -- call all clean & validation methods without capturing
        # -- their individual ValidationErrors
        try:
            self.clean_fields()

        except ValidationError as e:
            raise ValidationError(e.update_error_dict({}))

        try:
            self.clean()

        except ValidationError as e:
            raise ValidationError(e.update_error_dict({}))

        try:
            self.validate_unique()

        except ValidationError as e:
            raise ValidationError(e.update_error_dict({}))

        return super(ValidatingModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class ExtraColumn(RawSQL):

    def __init__(self, sql, params, output_field=None):

        super(ExtraColumn, self).__init__(
            sql, params, output_field=output_field)

    def get_group_by_cols(self):
        return []


class JSONSchemaValidator:

    validation_error_cls = ValidationError

    def __init__(self, schema):
        self.schema = schema

    def __call__(self, value):

        # -- multischema case
        if 'schemas' in self.schema:
            by_field = self.schema['by_field']
            schemas = self.schema['schemas']
            by_field_values = sorted(schemas.keys())

            self.validate_against_schema(
                object(**{by_field: enum(*by_field_values)}),
                {by_field: value[by_field]})

            for schema_key, schema in schemas.items():
                if value[by_field] == schema_key:
                    self.validate_against_schema(schema, value)

        # -- array multischema
        elif (self.schema.get('type') == 'array' and
                self.schema.get('items', {}).get('oneOf') and
                self.schema.get('items', {}).get('by_field')):

            # -- for now only support for the enum fields
            by_field = self.schema['items'].get('by_field')

            by_field_values = sorted([
                schema['properties'][by_field].get('const_value')
                for schema in self.schema['items']['oneOf']
            ])
            schemas_index = {
                schema['properties'][by_field].get('const_value'): schema
                for schema in self.schema['items']['oneOf']
            }

            # -- assert its an array
            self.validate_against_schema(array(object()), value)
            for item in value:
                fields = {by_field: enum(*by_field_values)}

                # -- assert required
                self.validate_against_schema(
                    object(**fields, required=[by_field]), item)

                # -- assert in enum
                self.validate_against_schema(
                    object(**fields), {by_field: item[by_field]})

                schema = schemas_index[item[by_field]]
                self.validate_against_schema(schema, item)

        # -- single schema case
        else:
            self.validate_against_schema(self.schema, value)

    def validate_against_schema(self, schema, value):
        try:
            json_validate(value, schema)

        except JsonValidationError as e:
            path = '.'.join([str(p) for p in e.path]) or '.'
            raise self.validation_error_cls(
                f"JSON did not validate. PATH: '{path}' REASON: {e.message}"
            )


class JSONSchemaField(JSONField):
    def __init__(self, *args, **kwargs):
        try:
            schema = kwargs.pop('schema')

        except KeyError:
            schema = {}

        super(JSONSchemaField, self).__init__(*args, **kwargs)
        self.validators.insert(0, JSONSchemaValidator(schema=schema))


class EnumChoiceField(models.CharField):

    def __init__(self, *args, enum_name=None, enum=None, **kwargs):

        self.enum_name = None
        if enum_name:
            self.enum_name = enum_name

        if enum:
            self.enum_name = enum.__name__
            kwargs['choices'] = [(e.value, e.value) for e in enum]

        # -- setting dynamical max_length
        if not kwargs.get('max_length'):
            max_length = 0
            for choice in kwargs['choices']:
                if len(str(choice[0])) > max_length:
                    max_length = len(str(choice[0]))

            kwargs['max_length'] = 2 ** math.ceil(math.log2(max_length))

        super(EnumChoiceField, self).__init__(*args, **kwargs)

    def deconstruct(self):

        name, path, args, kwargs = super().deconstruct()
        kwargs['enum_name'] = self.enum_name

        return name, path, args, kwargs


#
# Helper class for building easier to read JSON schema
#
def null_or(other):
    return {
        'oneOf': [
            {
                'type': 'null',
            },
            other,
        ],
    }


def null():
    return {
        'type': 'null',
    }


def string(
        pattern=None,
        minLength=None,  # noqa
        maxLength=None):  # noqa
    schema = {
        'type': 'string',
    }

    if pattern is not None:
        schema['pattern'] = pattern

    if minLength is not None:
        schema['minLength'] = minLength

    if maxLength is not None:
        schema['maxLength'] = maxLength

    return schema


def const(value):
    return {
        'type': 'string',
        'const': value,
        'pattern': f'^{value}$'
    }


def number(
        multipleOf=None,  # noqa
        minimum=None,
        exclusiveMinimum=None,  # noqa
        maximum=None,
        exclusiveMaximum=None):  # noqa

    schema = {
        'type': 'number',
    }

    if multipleOf is not None:
        schema['multipleOf'] = multipleOf

    if minimum is not None:
        schema['minimum'] = minimum

    if exclusiveMinimum is not None:
        schema['exclusiveMinimum'] = exclusiveMinimum

    if maximum is not None:
        schema['maximum'] = maximum

    if exclusiveMaximum is not None:
        schema['exclusiveMaximum'] = exclusiveMaximum

    return schema


def boolean():
    return {
        'type': 'boolean',
    }


def url():
    return {
        'type': 'string',
        'format': 'url',
    }


def enum(*enums, enum_name=None, const=None):

    if len(enums) == 1 and isinstance(enums[0], EnumMeta):
        enum = enums[0]
        enum_name = enum.__name__
        enums = [e.value for e in enum]

    if isinstance(enums[0], int):
        _type = 'integer'

    else:
        _type = 'string'

    output = {
        'type': _type,
        'enum_name': enum_name,
        'enum': list(enums),
    }

    if const:
        output['const_value'] = const

    return output


def object(dependencies=None, required=None, **properties):
    schema = {
        'type': 'object',
        'properties': properties,
    }

    if required:
        schema['required'] = required

    if dependencies:
        schema['dependencies'] = dependencies

    return schema


def dependencies(**deps):
    return deps


def array(items, extra=None):
    extra = extra or {}

    return {
        'type': 'array',
        'items': items,
        **extra,
    }


def multischema(schemas, by_field):
    return {
        'schemas': schemas,
        'by_field': by_field,
        'oneOf': list(schemas.values()),
    }


def one_of(*schemas, by_field=None):
    return {
        'oneOf': list(schemas),
        'by_field': by_field,
    }


import os

from django.core.validators import (
    URLValidator,
)
from django.core.exceptions import ValidationError


NULL = 'NULL'


def not_null_validator(value):

    message = 'Null value are not allowed'

    if value is None:
        raise ValidationError(message)


class BaseField:

    def __init__(self, required=True, default=None, allow_null=False):
        self.required = required
        self.default = default
        self.allow_null = allow_null

    def serialize(self, value):

        if not self.allow_null:
            not_null_validator(value)

        elif value is None and self.allow_null:
            return NULL


class CharField(BaseField):

    def __init__(self, max_length=None, **kwargs):
        self.max_length = max_length
        super(CharField, self).__init__(**kwargs)

    def serialize(self, value):

        # -- base validation
        serialized = super(CharField, self).serialize(value)
        if serialized == NULL:
            return None

        return value


class BooleanField(BaseField):

    def serialize(self, value):

        # -- base validation
        serialized = super(BooleanField, self).serialize(value)
        if serialized == NULL:
            return None

        if isinstance(value, bool):
            return value

        return value.upper() == 'TRUE'


class URLField(BaseField):

    def serialize(self, value):

        # -- base validation
        serialized = super(URLField, self).serialize(value)
        if serialized == NULL:
            return None

        URLValidator()(value)

        return value


class IntegerField(BaseField):

    def serialize(self, value):

        # -- base validation
        serialized = super(IntegerField, self).serialize(value)
        if serialized == NULL:
            return None

        return int(value)


class Env:
    """
    Class which captures all already validated and discovered environment
    variables.

    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class EnvParser:

    def __init__(self):

        env_variables = {}
        for field_name, field in self.fields.items():
            if field.required:
                raw_value = os.environ[field_name.upper()]

            else:
                raw_value = os.environ.get(
                    field_name.upper(), field.default)

            env_variables[field_name] = field.serialize(raw_value)

        self.env_variables = env_variables

    @property
    def fields(self):
        fields = {}
        for name in dir(self):
            if name != 'fields':
                attr = getattr(self, name)
                if isinstance(attr, BaseField):
                    fields[name] = attr

        return fields

    def parse(self):
        return Env(**self.env_variables)

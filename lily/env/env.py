
import os

from rest_framework import serializers as drf_serializers
from rest_framework.serializers import empty

from lily.base.events import EventFactory
from lily.base.serializers import *  # noqa


class Env:
    """
    Class which captures all already validated and discovered environment
    variables.

    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class EnvParser(drf_serializers.Serializer, EventFactory):

    def __init__(self):

        env_variables = {}
        for field_name, field in self.fields.items():
            if field.required:
                env_variables[field_name] = os.environ[field_name.upper()]

            else:
                default = field.default
                if default is empty:
                    default = None

                env_variables[field_name] = os.environ.get(
                    field_name.upper(), default)

        super(EnvParser, self).__init__(data=env_variables)

    def parse(self):
        if not self.is_valid():
            raise self.BrokenRequest(
                'ENV_DID_NOT_VALIDATE',
                data={'errors': self.errors})

        else:
            return Env(**self.data)

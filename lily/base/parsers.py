
from enum import Enum, unique

from rest_framework import serializers as drf_serializers

# -- needed for correct namespacing so that one could access all
# -- serializers stuff as a part of the `parsers` namespace
from .serializers import *  # noqa


@unique
class ParserTypeEnum(Enum):

    BODY = 'BODY'

    QUERY = 'QUERY'

    HEADER = 'HEADER'


class Parser(drf_serializers.Serializer):
    """Parses all types of payload: body, query, headers (future)."""

    @classmethod
    def as_query_parser(cls, *args, **kwargs):
        return cls(*args, parser_type=ParserTypeEnum.QUERY.value, **kwargs)

    @classmethod
    def as_body_parser(cls, *args, **kwargs):
        return cls(*args, parser_type=ParserTypeEnum.BODY.value, **kwargs)

    def __init__(
            self,
            *args,
            parser_type=ParserTypeEnum.BODY.value,
            **kwargs):

        raw_data = kwargs.get('data')
        if raw_data is None:
            kwargs['data'] = {}

        if parser_type == ParserTypeEnum.QUERY.value:
            kwargs['data'] = self.prepare_query_data(raw_data)

        elif parser_type == ParserTypeEnum.BODY.value:
            kwargs['data'] = self.prepare_body_data(raw_data)

        super(Parser, self).__init__(*args, **kwargs)

    def prepare_query_data(self, raw_data):

        data = {}
        if raw_data is not None:
            for field_name, field_class in self.fields.items():

                if not isinstance(field_class, ListField):  # noqa
                    try:
                        data[field_name] = raw_data[field_name]

                    # -- ignore key errors since they all will be caught
                    # -- by the validation
                    except (KeyError, IndexError):
                        pass

                else:
                    try:
                        data[field_name] = raw_data.getlist(field_name)

                    except AttributeError:
                        data[field_name] = raw_data.get(field_name)

        return data

    def prepare_body_data(self, raw_data):

        return raw_data


class PageParser(Parser):

    offset = IntegerField(default=0)  # noqa

    limit = IntegerField(default=100)  # noqa


class FullTextSearchParser(Parser):

    query = CharField(default=None)  # noqa


class ModelParser(drf_serializers.ModelSerializer, Parser):

    serializer_choice_field = EnumChoiceField  # noqa

    def build_standard_field(self, field_name, model_field):

        from . import models  # noqa - avoid circular dependency

        field_class, field_kwargs = super(
            ModelParser, self).build_standard_field(
                field_name, model_field)

        if isinstance(model_field, models.EnumChoiceField):
            field_kwargs['enum_name'] = model_field.enum_name
            field_class = EnumChoiceField  # noqa

        return field_class, field_kwargs

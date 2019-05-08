
from rest_framework import serializers as drf_serializers

# -- needed for correct namespacing so that one could access all
# -- serializers stuff as a part of the `parsers` namespace
from .serializers import *  # noqa


class QueryParser(drf_serializers.Serializer):

    def __init__(self, *args, **kwargs):

        raw_data = kwargs.get('data')

        if raw_data is not None:
            data = {}
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

            kwargs['data'] = data
            super(QueryParser, self).__init__(*args, **kwargs)


class PageQueryParser(QueryParser):

    offset = IntegerField(default=0)  # noqa

    limit = IntegerField(default=100)  # noqa


class FullTextSearchQueryParser(QueryParser):

    query = CharField(default=None)  # noqa


class BodyParser(drf_serializers.Serializer):
    pass


class ModelParser(drf_serializers.ModelSerializer):

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

# -*- coding: utf-8 -*-

from rest_framework import serializers as drf_serializers

# -- needed for correct namespacing so that one could access all
# -- serializers stuff as a part of the `parsers` namespace
from .serializers import *  # noqa


class ModelParser(drf_serializers.ModelSerializer):
    pass


class QueryParser(drf_serializers.Serializer):

    def __init__(self, *args, **kwargs):

        raw_data = kwargs.get('data')

        if raw_data is not None:
            data = {}
            for field_name, field_class in self.fields.items():

                if not isinstance(field_class, ListField):
                    try:
                        data[field_name] = raw_data[field_name]

                    # -- ignore key errors since they all will be caught
                    # -- by the validation
                    except (KeyError, IndexError):
                        pass

                else:
                    data[field_name] = raw_data.getlist(field_name)

            kwargs['data'] = data
            super(QueryParser, self).__init__(*args, **kwargs)


class PageQueryParser(QueryParser):

    offset = IntegerField(default=0)

    limit = IntegerField(default=50)


class BodyParser(drf_serializers.Serializer):
    pass

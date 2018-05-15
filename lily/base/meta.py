# -*- coding: utf-8 -*-

import re

from . import serializers


class Domain:

    def __init__(self, id, name):
        self.id = id.lower()
        self.name = name

    def __eq__(self, other):
        return (
            self.id == other.id and
            self.name == other.name)


class DomainSerializer(serializers.Serializer):

    _type = 'domain'

    id = serializers.CharField()

    name = serializers.CharField()


class Meta:

    def __init__(self, title, domain, description=None):
        self.title = title
        self.description = self.transform_description(description)
        self.domain = domain

    def transform_description(self, description):

        if description:
            description = description.strip()
            description = re.sub(r'[\n ]+', ' ', description)

        return description


class MetaSerializer(serializers.Serializer):

    _type = 'meta'

    title = serializers.CharField()

    description = serializers.CharField()

    domain = DomainSerializer()


import logging
import re

from lily.conf import settings
from . import serializers
from .events import EventFactory


logger = logging.getLogger()


class Domain(EventFactory):

    def __init__(self, id, name):
        if (len(id) > settings.LILY_MAX_DOMAIN_ID_LENGTH or
                re.search(r'\s+', id)):
            raise self.BrokenRequest(
                'BROKEN_ARGS_DETECTED',
                data={
                    'errors': {
                        'id': [
                            'should be shorter than {} characters and do '
                            'not contain white characters.'.format(
                                settings.LILY_MAX_DOMAIN_ID_LENGTH),
                        ]
                    }
                })
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

    def __eq__(self, other):
        return (
            self.title == other.title and
            self.description == other.description and
            self.domain == other.domain)

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

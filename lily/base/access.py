
from . import serializers


class Access:
    def __init__(self, access_list=None, is_private=False, is_external=False):
        self.is_private = is_private
        self.access_list = access_list
        self.is_external = is_external

    def __eq__(self, other):
        return (
            self.is_private == other.is_private and
            self.access_list == other.access_list and
            self.is_external == other.is_external)


class AccessSerializer(serializers.Serializer):

    _type = 'access'

    access_list = serializers.ListField(child=serializers.CharField())

    is_private = serializers.BooleanField()

    is_external = serializers.BooleanField()

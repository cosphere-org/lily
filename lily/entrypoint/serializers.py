
from lily.base import serializers
from lily.base.meta import MetaSerializer
from lily.base.source import SourceSerializer
from lily.base.access import AccessSerializer


class CommandSerializer(serializers.Serializer):

    _type = 'command'

    method = serializers.ChoiceField(
        choices=('POST', 'GET', 'PUT', 'DELETE'))

    path_conf = serializers.JSONField()

    meta = MetaSerializer()

    access = AccessSerializer()

    source = SourceSerializer()

    schemas = serializers.JSONField(required=False)

    examples = serializers.JSONField(required=False)

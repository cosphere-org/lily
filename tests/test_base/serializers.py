
from unittest.mock import Mock

from lily.base import serializers
from .models import (
    Account,
    Person,
    MediaItemFile,
)
from .enums import MediaItemType, MediaItemUsageType


#
# CASE: SIMPLE SERIALIZER
#
class AccountPlainSerializer(serializers.Serializer):

    _type = 'account_plain'

    user_id = serializers.IntegerField()

    avatar_uri = serializers.CharField()

    username = serializers.CharField()


#
# CASE: SIMPLE SERIALIZER WITH ACCESS
#
class PersonSerializer(serializers.Serializer):

    _type = 'person'

    name = serializers.CharField(max_length=123, required=False)

    age = serializers.IntegerField(min_value=18)

    def get_access(self, instance):

        return [
            (Mock(command_conf={'name': 'MARK_IT'}), True),
            (Mock(command_conf={'name': 'REMOVE_IT'}), False),
            ('ALLOW_IT', False),
        ]


#
# CASE: SIMPLE MODEL SERIALIZER WITH ACCESS
#
class PersonModelSerializer(serializers.ModelSerializer):

    _type = 'person'

    def get_access(self, instance):

        return [
            (Mock(command_conf={'name': 'MARK_IT'}), True),
            (Mock(command_conf={'name': 'REMOVE_IT'}), False),
            ('ALLOW_IT', False),
        ]

    class Meta:
        model = Person
        fields = ('name', 'age')


#
# CASE: MODEL SERIALIZER WITH ENUM & SERIALIZER METHOD FIELD
#
class AccountSerializer(serializers.ModelSerializer):

    _type = 'account'

    email = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = (
            'user_id',
            'atype',
            'freemium_till_datetime',
            'show_in_ranking',
            'email',
        )

    def get_email(self, instance) -> str:

        user_id = self.context['request'].access['user_id']

        if user_id == instance.user_id:
            return instance.user_email

        return None


#
# CASE: NESTED SERIALIZERS AND MANY
#
class MediaItemFileSerializer(serializers.ModelSerializer):

    _type = 'mediaitem_file'

    class Meta:
        model = MediaItemFile

        fields = (
            'id',
            'content_type',
            'file_uri')


class MediaItemSerializer(serializers.Serializer):

    _type = 'mediaitem'

    id = serializers.IntegerField()

    original = MediaItemFileSerializer()

    files = MediaItemFileSerializer(many=True)

    type = serializers.EnumChoiceField(enum=MediaItemType)

    usage_type = serializers.EnumChoiceField(enum=MediaItemUsageType)

    text = serializers.CharField()

    reference = serializers.JSONField()

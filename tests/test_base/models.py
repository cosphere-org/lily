
from django.db import models

from lily.base.models import EnumChoiceField
from .enums import AccountType


class Account(models.Model):

    user_id = models.IntegerField()

    atype = EnumChoiceField(
        default=AccountType.FREE.value,
        enum=AccountType)

    freemium_till_datetime = models.DateTimeField()

    show_in_ranking = models.BooleanField()

    class Meta:
        app_label = 'base'


class MediaItemFile(models.Model):

    file_uri = models.URLField()

    content_type = models.TextField()

    class Meta:
        app_label = 'base'


class Person(models.Model):

    name = models.CharField(max_length=100)

    age = models.IntegerField(null=True, blank=True)

    is_ready = models.BooleanField()

    class Meta:
        app_label = 'base'

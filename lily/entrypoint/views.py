# -*- coding: utf-8 -*-

from django.views.generic import View
from django.conf import settings

from lily.base import serializers, name
from lily.base.command import command
from lily.base.meta import Meta, Domain
from lily.base.access import Access
from lily.base.output import Output
from lily.base import config


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# FIXME: here I should serve names of all COMMANDS that current services
# enables + their external dependencies!!!!!
class EntryPointView(View):

    class EntryPointSerializer(serializers.Serializer):

        _type = 'entrypoint'

        version = serializers.CharField()

    @command(
        name=name.Read('ENTRY_POINT'),

        meta=Meta(
            title='Entry Point View',
            domain=Domain(id='EntryPoint', name='EntryPoint Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_ENTRYPOINT_VIEWS_ACCESS_LIST),

        output=Output(
            serializer=EntryPointSerializer),
    )
    def get(self, request):

        raise self.event.Read({'version': config.version})

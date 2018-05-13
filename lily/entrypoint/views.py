# -*- coding: utf-8 -*-

from django.views.generic import View
from django.conf import settings

from base import serializers, name
from base.command import command
from base.meta import Meta, Domain
from base.access import Access
from base.output import Output
from base import config


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

# -*- coding: utf-8 -*-

from django.views.generic import View
from django.conf import settings

from base import serializers, name as n
from base.command import command
from base.meta import Meta, Domain
from base.access import Access
from base.output import Output


class EntryPointView(View):

    class EntryPointSerializer(serializers.Serializer):

        _type = 'entrypoint'

        version = serializers.CharField()

    @command(
        name=n.Read('Entry Point'),

        meta=Meta(
            title='Entry Point View',
            domain=Domain(id='EntryPoint', name='EntryPoint Management')),

        access=Access(
            access_list=settings.LILY_ENTRYPOINT_VIEWS_ACCESS_LIST),

        output=Output(
            serializer=EntryPointSerializer),
    )
    def get(self, request):

        raise self.event.Read({'version': self.get_version()})

    def get_version(self):
        return settings.LILY_SERVICE_VERSION

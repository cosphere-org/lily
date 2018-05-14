# -*- coding: utf-8 -*-

from importlib import import_module

from django.views.generic import View
from django.conf import settings

from lily.base import serializers, name
from lily.base.command import command
from lily.base.meta import Meta, Domain
from lily.base.access import Access
from lily.base.output import Output
from .renderers.commands import CommandsRenderer
from lily.base import config


class EntryPointView(View):

    class EntryPointSerializer(serializers.Serializer):
        _type = 'entrypoint'

        version = serializers.CharField()

        commands = serializers.JSONField()

    @command(
        name=name.Read('ENTRY_POINT'),

        meta=Meta(
            title='Read Entry Point',
            description='''
                Serve Service Entry Point data:
                - current version of the service
                - list of all available commands together with their
                  configuration
                - examples collected for a given service.

            ''',
            domain=Domain(id='docs', name='Docs Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_DOCS_VIEWS_ACCESS_LIST),

        output=Output(serializer=EntryPointSerializer),
    )
    def get(self, request):

        raise self.event.Read(
            {
                'version': config.version,
                'commands': CommandsRenderer(self.get_urlpatterns()).render(),
            })

    def get_urlpatterns(self):
        return import_module(settings.ROOT_URLCONF).urlpatterns

# -*- coding: utf-8 -*-

from importlib import import_module

from django.views.generic import View
from django.conf import settings

from lily.base import serializers, name
from lily.base.command import command
from lily.base.meta import Meta, Domain
from lily.base.access import Access
from lily.base.output import Output
from .renderers.typescript import CommandsRenderer


class CommandsView(View):

    class CommandsSerializer(serializers.Serializer):
        _type = 'commands_list'

        commands = serializers.JSONField()

    @command(
        name=name.BulkRead('COMMANDS'),

        meta=Meta(
            title='Serve Commands spec',
            description='''
                It serves spec of all available commands in the form that is
                easily consumable by any 3rd party consumers that might want
                to work with such data in order to transform it to some desired
                form.

            ''',
            domain=Domain(id='docs', name='Docs Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_DOCS_VIEWS_ACCESS_LIST),

        output=Output(serializer=CommandsSerializer),
    )
    def get(self, request):

        raise self.event.BulkRead(
            {'commands': CommandsRenderer(self.get_urlpatterns()).render()})

    def get_urlpatterns(self):
        return import_module(settings.ROOT_URLCONF).urlpatterns


# FIXME: this still requires some extra work!!!
class BlueprintSpecView(View):

    class BlueprintSpecSerializer(serializers.Serializer):
        _type = 'commands_config'

        spec = serializers.JSONField()

    @command(
        name=name.Read('BLUEPRINT_SPEC'),

        meta=Meta(
            title='Serve Blueprint spec for the Blueprint docs generator',
            description='''
                It serves all publicly available commands and their
                configuration served in the form easily consumable by the
                Blueprint Docs generator.

            ''',
            domain=Domain(id='docs', name='Docs Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_DOCS_VIEWS_ACCESS_LIST),

        output=Output(serializer=BlueprintSpecSerializer),
    )
    def get(self, request):

        raise self.event.Read({'spec': {}})

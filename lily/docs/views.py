# -*- coding: utf-8 -*-

from importlib import import_module

from django.views.generic import View
from django.conf import settings

from lily.base import serializers, name
from lily.base.command import command
from lily.base.meta import Meta, Domain
from lily.base.access import Access
from lily.base.output import Output
from .renderers.typescript import TypeScriptSpecRenderer


class TypeScriptSpecView(View):

    class TypeScriptSpecSerializer(serializers.Serializer):
        _type = 'typescript_spec'

        spec = serializers.JSONField()

    @command(
        name=name.Read('TYPESCRIPT_SPEC'),

        meta=Meta(
            title='Serve TypeScript spec required by the TypeScript client',
            description='''
                It serves all publicly available commands and their
                configuration served in the form easily consumable by the
                TypeScript Client generator.

            ''',
            domain=Domain(id='docs', name='Docs Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_DOCS_VIEWS_ACCESS_LIST),

        output=Output(serializer=TypeScriptSpecSerializer),
    )
    def get(self, request):

        raise self.event.Read(
            {'spec': TypeScriptSpecRenderer(self.get_urlpatterns()).render()})

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

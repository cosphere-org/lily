# -*- coding: utf-8 -*-

from django.views.generic import View
from django.conf import settings

from lily.base import serializers, parsers, name
from lily.base.command import command
from lily.base.meta import Meta, MetaSerializer, Domain
from lily.base.source import SourceSerializer
from lily.base.access import Access, AccessSerializer
from lily.base.input import Input
from lily.base.output import Output
from .renderers.commands import CommandsRenderer
from lily.base import config


class CommandSerializer(serializers.Serializer):

    _type = 'command'

    method = serializers.ChoiceField(
        choices=('post', 'get', 'put', 'delete'))

    path_conf = serializers.JSONField()

    meta = MetaSerializer()

    access = AccessSerializer()

    source = SourceSerializer()

    schemas = serializers.JSONField()

    examples = serializers.JSONField(required=False)


class EntryPointView(View):

    class EntryPointSerializer(serializers.Serializer):
        _type = 'entrypoint'

        version = serializers.CharField()

        commands = CommandSerializer(many=True)

    class QueryParser(parsers.QueryParser):

        # FIXME: test it!!!
        commands = parsers.ListField(child=parsers.CharField(), default=None)

        with_schemas = parsers.BooleanField(default=True)

        with_examples = parsers.BooleanField(default=False)

    @command(
        name=name.Read('ENTRY_POINT'),

        meta=Meta(
            title='Read Entry Point',
            description='''
                Serve Service Entry Point data:
                - current version of the service
                - list of all available commands together with their
                  configurations
                - examples collected for a given service.

            ''',
            domain=Domain(id='docs', name='Docs Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_DOCS_VIEWS_ACCESS_LIST),

        input=Input(query_parser=QueryParser),

        output=Output(serializer=EntryPointSerializer),
    )
    def get(self, request):

        command_names = request.input.query['commands']

        with_schemas = request.input.query['with_schemas']

        with_examples = request.input.query['with_examples']

        commands = CommandsRenderer(with_examples).render()
        if command_names:
            commands = {
                command_name: commands[command_name]
                for command_name in command_names}

        if not with_schemas:
            for c in commands:
                del c['schema']

        raise self.event.Read(
            {
                'version': config.version,
                'commands': commands,
            })

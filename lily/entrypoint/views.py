# -*- coding: utf-8 -*-

import json
import os

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


def get_cache_filepath():
    return os.path.join(settings.LILY_CACHE_DIR, 'commands.json')


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


class EntryPointView(View):

    class EntryPointSerializer(serializers.Serializer):
        _type = 'entrypoint'

        version = serializers.CharField()

        name = serializers.CharField()

        commands = serializers.DictField(child=CommandSerializer())

    class QueryParser(parsers.QueryParser):

        commands = parsers.ListField(child=parsers.CharField(), default=None)

        with_schemas = parsers.BooleanField(default=True)

        with_examples = parsers.BooleanField(default=False)

        is_private = parsers.BooleanField(default=None)

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
            access_list=settings.LILY_ENTRYPOINT_VIEWS_ACCESS_LIST),

        input=Input(query_parser=QueryParser),

        output=Output(serializer=EntryPointSerializer),
    )
    def get(self, request):

        command_names = request.input.query['commands']

        with_schemas = request.input.query['with_schemas']

        with_examples = request.input.query['with_examples']

        is_private = request.input.query['is_private']

        commands = self.get_commands()

        if command_names:
            commands = {
                command_name: commands[command_name]
                for command_name in command_names}

        for c in commands.values():
            if not with_schemas:
                del c['schemas']

            if not with_examples:
                del c['examples']

        if is_private is not None:
            commands = {
                name: command
                for name, command in commands.items()
                if command['access']['is_private'] == is_private}

        raise self.event.Read(
            {
                'name': config.name,
                'version': config.version,
                'commands': commands,
            })

    # FIXME: !!! this could be easily moved to some generic class and
    # I could use it as a poor's man cache just before the response
    def get_commands(self):
        cache_filepath = get_cache_filepath()

        # -- attempt to fetch `commands` from the local cache. If successful
        # -- check if it was rendered for the newest version of the service
        try:
            with open(cache_filepath, 'r') as f:
                data = json.loads(f.read())

                if data['version'] == config.version:
                    return data['commands']

        except FileNotFoundError:
            pass

        # -- if reached here there were no `commands` or they were outdated
        commands = CommandsRenderer().render()
        commands = {
            name: CommandSerializer(conf).data
            for name, conf in commands.items()
        }

        # -- save in the cache for the future reference
        with open(cache_filepath, 'w') as f:
            f.write(json.dumps({
                'version': config.version,
                'commands': commands,
            }))

        return commands

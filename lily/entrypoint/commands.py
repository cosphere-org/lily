
import os
import json

from lily.conf import settings
from lily.base import serializers, parsers, name
from lily.base.command import command
from lily.base.commands import HTTPCommands
from lily.base.meta import Meta, Domain
from lily.base.access import Access
from lily.base.input import Input
from lily.base.output import Output
from .serializers import CommandSerializer
from lily.shared import get_lily_path, get_version


class EntryPointCommands(HTTPCommands):

    class EntryPointSerializer(serializers.Serializer):

        class VersionInfoSerializer(serializers.Serializer):

            _type = 'version_info'

            deployed = serializers.CharField()

            displayed = serializers.CharField()

            available = serializers.ListField(child=serializers.CharField())

        _type = 'entrypoint'

        version_info = VersionInfoSerializer()

        name = serializers.CharField()

        commands = serializers.DictField(child=CommandSerializer())

        enums = serializers.ListField(child=serializers.DictField())

    class QueryParser(parsers.Parser):

        commands = parsers.ListField(child=parsers.CharField(), default=None)

        with_schemas = parsers.BooleanField(default=True)

        is_private = parsers.BooleanField(default=None)

        domain_id = parsers.CharField(default=None)

        version = parsers.CharField(default=None)

    @command(
        name=name.Read('ENTRY_POINT'),

        meta=Meta(
            title='Read Entry Point',
            description='''
                Serve Service Entry Point data:
                - current or chosen version of the service
                - list of all available commands together with their
                  configurations
                - examples collected for a given service.

            ''',
            domain=Domain(id='docs', name='Docs Management')),

        access=Access(
            is_private=True,
            access_list=settings.LILY_ENTRYPOINT_COMMANDS_ACCESS_LIST),

        input=Input(query_parser=QueryParser),

        output=Output(serializer=EntryPointSerializer),
    )
    def get(self, request):

        command_names = request.input.query['commands']

        is_private = request.input.query['is_private']

        domain_id = request.input.query['domain_id']

        version = request.input.query['version']

        commands = self.get_commands(version)
        enums = commands.pop('enums')

        if command_names:
            commands = {
                command_name: commands[command_name]
                for command_name in command_names}

        if is_private is not None:
            commands = {
                name: command
                for name, command in commands.items()
                if command['access']['is_private'] == is_private
            }

        if domain_id:
            commands = {
                name: command
                for name, command in commands.items()
                if command['meta']['domain']['id'].lower() == domain_id.lower()
            }

        raise self.event.Read(
            {
                'name': 'name',
                'version_info': {
                    'deployed': get_version(),
                    'displayed': version or get_version(),
                    'available': self.get_available_versions(),
                },
                'commands': commands,
                'enums': enums,
            })

    def get_available_versions(self):

        commands_dir_path = os.path.join(get_lily_path(), 'commands')

        return sorted(
            [
                commands_file.replace('.json', '')
                for commands_file in os.listdir(commands_dir_path)
            ],
            key=lambda x: [int(e) for e in x.split('.')],
            reverse=True)

    def get_commands(self, version=None):

        version = version or get_version()
        commands_dir_path = os.path.join(get_lily_path(), 'commands')

        commands_path = os.path.join(commands_dir_path, f'{version}.json')
        with open(commands_path, 'r') as f:
            return json.loads(f.read())

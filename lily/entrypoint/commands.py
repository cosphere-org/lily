
from lily.conf import settings
from lily.base import serializers, parsers, name
from lily.base.command import command
from lily.base.commands import HTTPCommands
from lily.base.meta import Meta, MetaSerializer, Domain
from lily.base.source import SourceSerializer
from lily.base.access import Access, AccessSerializer
from lily.base.input import Input
from lily.base.output import Output
from .renderers.commands import CommandsRenderer
from lily.base.conf import Config


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


class EntryPointCommands(HTTPCommands):

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

        domain_id = parsers.CharField(default=None)

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
            access_list=settings.LILY_ENTRYPOINT_COMMANDS_ACCESS_LIST),

        input=Input(query_parser=QueryParser),

        output=Output(serializer=EntryPointSerializer),
    )
    def get(self, request):

        command_names = request.input.query['commands']

        with_schemas = request.input.query['with_schemas']

        with_examples = request.input.query['with_examples']

        is_private = request.input.query['is_private']

        domain_id = request.input.query['domain_id']

        config = Config()

        commands = self.get_commands(config=config)

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
                'name': config.name,
                'version': config.version,
                'commands': commands,
            })

    def get_commands(self, config):

        # -- if reached here there were no `commands` or they were outdated
        commands = CommandsRenderer().render()
        return {
            name: CommandSerializer(conf).data
            for name, conf in commands.items()
        }

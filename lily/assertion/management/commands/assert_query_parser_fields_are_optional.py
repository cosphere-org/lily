
import os
import json

from lily.conf import settings
from lily.shared import get_lily_path, get_version
from django.core.management import CommandError
import djclick as click


@click.command()
def command():

    commands_dir = os.path.join(get_lily_path(), 'commands')

    excluded = (
        settings.LILY_EXCLUDE_QUERY_PARSER_ALL_OPTIONAL_ASSERTIONS or [])
    with open(os.path.join(commands_dir, f'{get_version()}.json'), 'r') as f:
        commands = json.loads(f.read())

        for name, command in commands.items():
            if name in excluded or name == 'enums':
                continue

            input_query = command['schemas'].get(
                'input_query',
                {'schema': {'required': []}})

            if input_query['schema']['required']:
                fields = ','.join(input_query['schema']['required'])

                raise CommandError(
                    f"ERROR: query parser for '{name}' has some not optional "
                    f"fields: [{fields}]")

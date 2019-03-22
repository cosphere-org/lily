
import click

import os
import json


@click.command()
def assert_query_parser_fields_are_optional():

    base_dir = os.getcwd()

    lily_dir = os.path.join(base_dir, '.lily')

    commands_dir = os.path.join(base_dir, '.lily', 'commands')

    with open(os.path.join(lily_dir, 'config.json')) as f:
        config = json.loads(f.read())
        version = config['version']

    with open(os.path.join(commands_dir, f'{version}.json'), 'r') as f:
        commands = json.loads(f.read())

        for name, command in commands.items():
            input_query = command['schemas'].get(
                'input_query',
                {'schema': {'required': []}})

            if input_query['schema']['required']:
                fields = ','.join(input_query['schema']['required'])

                raise click.ClickException(
                    f"ERROR: query parser for '{name}' has some not optional "
                    f"fields: [{fields}]")

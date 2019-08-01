
import json
import os

from lily_assistant.config import Config
from django.core import management
import djclick as click


@click.command()
@click.argument('v', type=str)
def command(v):

    config = Config()

    migrations_dir_path = os.path.join(config.get_lily_path(), 'migrations')

    migrations_path = os.path.join(migrations_dir_path, f'{v}.json')
    with open(migrations_path, 'r') as f:
        migrations_plan = json.loads(f.read())['plan']

    for app_name, migration in migrations_plan:
        management.call_command('migrate', app_name, migration)

    click.secho(
        f'Migrations plan for version {v} applied.',
        fg='green')

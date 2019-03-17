
import json
import os

import djclick as click
from lily_assistant.config import Config

from ...renderers.commands import CommandsRenderer
from ...serializers import CommandSerializer


@click.command()
def command():
    """Render all commands spec.

    Render all commands with their spec, examples, schemas etc. so far created
    for a current version of the service.

    """

    config = Config()

    commands_dir_path = os.path.join(Config.get_lily_path(), 'commands')
    if not os.path.exists(commands_dir_path):
        os.mkdir(commands_dir_path)

    commands_path = os.path.join(commands_dir_path, f'{config.version}.json')
    with open(commands_path, 'w') as f:
        commands = CommandsRenderer().render()
        f.write(
            json.dumps(
                {
                    name: CommandSerializer(conf).data
                    for name, conf in commands.items()
                },
                indent=4,
                sort_keys=False))

    click.secho(
        f'Commands rendered for to file {commands_path}',
        fg='green')

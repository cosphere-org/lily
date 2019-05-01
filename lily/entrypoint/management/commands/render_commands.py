
import json
import os

import djclick as click
from lily_assistant.config import Config

from ...renderer import CommandsRenderer
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

    version = config.next_version or config.version
    commands_path = os.path.join(commands_dir_path, f'{version}.json')
    with open(commands_path, 'w') as f:
        commands = CommandsRenderer().render()
        enums = commands.pop('@enums')

        commands = {
            name: CommandSerializer(conf).data
            for name, conf in commands.items()
        }
        f.write(
            json.dumps(
                {
                    **commands,
                    '@enums': enums,
                },
                indent=4,
                sort_keys=False))

    click.secho(
        f'Commands rendered for to file {commands_path}',
        fg='green')

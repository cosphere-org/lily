
import os

from lily_assistant.config import Config
import djclick as click


@click.command()
def command():

    examples_path = os.path.join(Config.get_lily_path(), 'examples.json')

    try:
        os.remove(examples_path)

    except FileNotFoundError:
        pass

    click.echo("'examples.json' was removed")

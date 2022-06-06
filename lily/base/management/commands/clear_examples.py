
import os

from lily.shared import get_lily_path
import djclick as click


@click.command()
def command():

    examples_path = os.path.join(get_lily_path(), 'examples.json')

    try:
        os.remove(examples_path)

    except FileNotFoundError:
        pass

    click.echo("'examples.json' was removed")

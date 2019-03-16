
import textwrap

import click


class Logger:

    def info(self, text):

        text = textwrap.dedent(text).strip()
        click.secho('[INFO]\n\n{text}'.format(text=text), fg='yellow')

    def error(self, text):

        text = textwrap.dedent(text).strip()
        click.secho('[ERROR]\n\n{text}'.format(text=text), fg='red')

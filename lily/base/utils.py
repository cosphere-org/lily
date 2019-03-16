
import importlib
import re
from time import time


def import_from_string(path):
    """Attempt to import a class from a string representation.

    From: django rest_framework

    """
    try:
        parts = path.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    except ImportError as e:
        msg = "Could not import '{}' for setting. {}: {}.".format(
            path, e.__class__.__name__, e)
        raise ImportError(msg)


def normalize_indentation(text, min_indent=4):
    """Normalize text so that it's indented by specific amount.

    The minimal indent would be `min_indent`.

    """

    # -- trim beginning and ending
    text = re.sub(r'^\s*\n', '', text)
    text = re.sub(r'\n\s*$', '', text)

    # -- remove minimal indentation
    lines = text.split('\n')
    try:
        base_indent = min([
            len(re.match(r'\s*', line).group())
            for line in lines
            if line != ''])

    except ValueError:
        base_indent = 0

    pattern = re.compile('^\\s{{{}}}'.format(base_indent))
    lines = [pattern.sub('', line) for line in lines]

    # -- add `min_indent`
    lines = [min_indent * ' ' + line for line in lines]
    return '\n'.join(lines)


class Timer:

    def __init__(self):
        self.start = time()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    @property
    def elapsed(self):
        total_seconds = time() - self.start

        # -- hours
        hours = int(total_seconds // 3600)
        total_seconds = total_seconds - 3600 * hours

        # -- minutes
        minutes = int(total_seconds // 60)
        total_seconds = total_seconds - 60 * minutes

        # -- seconds
        seconds = int(total_seconds)
        total_seconds = total_seconds - int(total_seconds)

        # -- miliseconds
        miliseconds = int(round(1000 * total_seconds, 3))

        return '{hours}:{minutes}:{seconds}.{miliseconds}'.format(
            hours=str(hours).rjust(2, '0'),
            minutes=str(minutes).rjust(2, '0'),
            seconds=str(seconds).rjust(2, '0'),
            miliseconds=str(miliseconds).rjust(3, '0'))

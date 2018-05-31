# -*- coding: utf-8 -*-

import importlib
import re


def import_from_string(path):
    """
    Attempt to import a class from a string representation.

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
    """
    Normalizes text so that it's indented by the amount specified
    by `min_indent`.

    """

    # -- trim beginning and ending
    text = re.sub('^\s*\n', '', text)
    text = re.sub('\n\s*$', '', text)

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

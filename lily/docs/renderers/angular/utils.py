# -*- coding: utf-8 -*-

import re


def to_camelcase(text, first_lower=False):
    tokens = re.split(r'\_+', text)

    camel_text = ''.join([token.capitalize() for token in tokens])

    if camel_text and first_lower:
        camel_text = camel_text[0].lower() + camel_text[1:]

    return camel_text


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

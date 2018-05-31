# -*- coding: utf-8 -*-

import re


def to_camelcase(text, first_lower=False):
    tokens = re.split(r'\_+', text)

    camel_text = ''.join([token.capitalize() for token in tokens])

    if camel_text and first_lower:
        camel_text = camel_text[0].lower() + camel_text[1:]

    return camel_text

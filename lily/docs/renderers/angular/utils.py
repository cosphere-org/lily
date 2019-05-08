
import re


def capitalize(t):

    if len(t) > 1:
        return t[0].upper() + t[1:]

    return t.upper()


def to_camelcase(text, first_lower=False):

    if text == text.upper():
        text = text.lower()

    tokens = re.split(r'\_+', text)

    camel_text = ''.join([capitalize(token) for token in tokens])

    if camel_text and first_lower:
        camel_text = camel_text[0].lower() + camel_text[1:]

    return camel_text

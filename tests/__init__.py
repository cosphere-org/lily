
import re


def remove_white_chars(text):
    return re.sub(r'\s+', '', text)


import re


HASHTAG_ESCAPE_SEQUENCE = 'HASH58437HASH'
"""
Sequence of characters which will be used to replace # character appearing
in front of any word transforming it into hashtag.

Default behaviour of data base strips away the hash character and stems
the hashtag word therefore making usage of hashtags as filters impossible. To
prevent this default behaviour the sequence ``HASHTAG_ESCAPE_SEQUENCE`` is
replaced in both searched text and query.

"""


HASHTAG_PATTERN = re.compile(
    r'(?P<prefix>'
    r'^|'  # either it appears at the beginning of string
    r'\s+|'  # or is preceded by space of any kind
    r'~|'  # or is preceded by negation
    r'['
    r':;,.!?。'  # or is preceded by punctuation
    r'’\[\]\(\)'  # or is preceded by brackets
    r'])(?P<hash>#)(?P<text>\w+)',
    flags=re.I | re.U)

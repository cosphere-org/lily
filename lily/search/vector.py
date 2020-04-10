
import re
from copy import deepcopy

from django.contrib.postgres.search import (
    SearchVector,
    SearchVectorCombinable,
    CombinedExpression,
)
from django.db import connection
from trans import trans
import hunspell

from .latex.transformer import transform as transform_latex
from .constants import HASHTAG_ESCAPE_SEQUENCE, HASHTAG_PATTERN
from .stopwords import stopwords_filter


class TextVector:

    hobj_pl = hunspell.HunSpell(
        '/usr/share/hunspell/pl_PL.dic',
        '/usr/share/hunspell/pl_PL.aff')

    def parse_to_tsvector(self, conf, text, weight=None):

        stems = self.parse(conf, text, weight)
        return self.to_tsvector(stems)

    def parse_to_list(self, conf, text, weight=None):

        stems = self.parse(conf, text, weight)
        return sorted(stems.keys())

    def parse(self, conf, text, weight=None):
        if text is None or not text.strip():
            return {}

        # -- transformers
        text = text.strip()
        text = self.transform_special_characters(text)
        text = self.transform_hashtags(text)
        text = self.transform_latex(conf, text)

        # -- tokens
        tokens = self.tokenize(conf, text)

        # -- stems
        stems = {}
        stems = self.augument_with_stems(conf, text, weight, stems, tokens)
        stems = self.augument_with_unaccents(conf, weight, stems, tokens)

        return stems

    #
    # SPECIAL CHARACTERS
    #
    def transform_special_characters(self, text):
        weird = [
            'ą', 'Ą', 'a\\u0328', 'A\\u0328',
            'ę', 'Ę', 'e\\u0328', 'E\\u0328',
            'ó', 'Ó', 'o\\u0301', 'O\\u0301',
            'ć', 'Ć', 'c\\u0301', 'C\\u0301',
            'ś', 'Ś', 's\\u0301', 'S\\u0301',
            'ż', 'Ż', 'z\\u0307', 'Z\\u0307',
            'ź', 'Ź', 'z\\u0301', 'Z\\u0301',
            'ń', 'Ń', 'n\\u0301', 'N\\u0301',
        ]
        normal = [
            'ą', 'Ą', '\u0105', '\u0104',
            'ę', 'Ę', '\u0119', '\u0118',
            'ó', 'Ó', '\xf3', '\xd3',
            'ć', 'Ć', '\u0107', '\u0106',
            'ś', 'Ś', '\u015b', '\u015a',
            'ż', 'Ż', '\u017c', '\u017b',
            'ź', 'Ź', '\u017a', '\u0179',
            'ń', 'Ń', '\u0144', '\u0143',
        ]

        for w, n in zip(weird, normal):
            text = text.replace(w, n)

        return text

    #
    # HASHTAGS
    #
    def transform_hashtags(self, text):
        def replace_hashtag(match):

            return "{prefix}{escape_seq}{text}".format(
                prefix=match.group('prefix'),
                escape_seq=HASHTAG_ESCAPE_SEQUENCE,
                text=match.group('text'))

        return HASHTAG_PATTERN.sub(replace_hashtag, text)

    #
    # LATEX
    #
    def transform_latex(self, conf, text):
        return transform_latex(text, conf)

    #
    # TOKENIZE
    #
    def tokenize(self, conf, text):
        with connection.cursor() as c:
            # deal with accents
            c.execute(
                "SELECT token FROM ts_debug(%s, %s) WHERE alias != 'blank'",
                [conf, text])

            tokens = [
                (t[0], i + 1)
                for i, t in enumerate(c.fetchall())]

        return [
            (token, position)
            for token, position in tokens
            if not stopwords_filter.is_stopword(conf, token)
        ]

    #
    # UNACCENTS
    #
    def augument_with_unaccents(self, conf, weight, stems, tokens):

        # -- unaccent original tokens
        for token, position in tokens:

            token = token.lower()
            unaccented_token = trans(token)
            if unaccented_token != token:
                stems.setdefault(unaccented_token, set())
                stems[unaccented_token] |= set([
                    self.get_position(position, weight)
                ])

        # -- unaccent stems
        for stem, positions in deepcopy(stems).items():

            stem = stem.lower()
            unaccented_stem = trans(stem)
            if unaccented_stem != stem:
                stems.setdefault(unaccented_stem, set())
                stems[unaccented_stem] |= positions

        return stems

    #
    # STEMS
    #
    def augument_with_stems(self, conf, text, weight, stems, tokens):

        if conf == 'polish':
            return self._augument_with_stems_polish(
                conf, weight, stems, tokens)

        else:
            return self._augument_with_stems_generic(conf, text, weight, stems)

    def _augument_with_stems_polish(self, conf, weight, stems, tokens):

        if conf == 'polish':
            for token, position in tokens:
                token_stems = self._get_polish_stems(token)
                for stem in token_stems:
                    stems.setdefault(stem, set())
                    stems[stem].add(self.get_position(position, weight))

        return stems

    def _get_polish_stems(self, token):
        token_stems = self.hobj_pl.stem(token)
        stems = []

        if token_stems:
            for stem in token_stems:
                stem = stem.decode(self.hobj_pl.get_dic_encoding())
                stems.append(stem.lower())

        else:
            stems.append(token.lower())

        return stems

    def _augument_with_stems_generic(self, conf, text, weight, stems):
        with connection.cursor() as c:
            if not weight:
                c.execute("SELECT to_tsvector(%s, %s)", [conf, text])

            else:
                c.execute(
                    "SELECT setweight(to_tsvector(%s, %s), %s)",
                    [conf, text, weight])

            tsstems = self.from_tsvestor(c.fetchone()[0])

        for stem, positions in tsstems.items():
            stems.setdefault(stem, set())
            stems[stem] = stems[stem] | positions

        return stems

    #
    # GENERAL
    #
    def get_position(self, i, weight):
        if weight:
            return f'{i}{weight}'

        else:
            return f'{i}'

    def from_tsvestor(self, tsvector):
        stems = {}
        for stem_pos in tsvector.split():
            stem, positions = stem_pos.split(':')

            stem = stem.strip()
            stem = re.sub(r"^'", '', stem)
            stem = re.sub(r"'$", '', stem)

            stems[stem] = set(positions.split(','))

        return stems

    def to_tsvector(self, stems):
        def join_positions(x):
            return ','.join([str(c) for c in x])

        return ' '.join([
            f"'{stem}':{join_positions(positions)}"
            for stem, positions in stems.items()
        ])


#
# HELPERS
#
def _concatenate_tsvectors(v1, v2):

    with connection.cursor() as c:
        c.execute("SELECT %s::tsvector || %s::tsvector", [v1, v2])

        return c.fetchone()[0]


def concatenate_tsvectors(*vectors):

    v1 = vectors[0]
    for v in vectors[1:]:
        v1 = _concatenate_tsvectors(v1, v)

    return v1


class VectorCombinable(SearchVectorCombinable):

    def _combine(self, other, connector, reversed, node=None):
        return CombinedVector(self, connector, other, self.config)


class CombinedVector(VectorCombinable, CombinedExpression):
    def __init__(self, lhs, connector, rhs, config, output_field=None):
        self.config = config
        super(
            CombinedVector,
            self).__init__(lhs, connector, rhs, output_field)


class StoredVector(SearchVector, VectorCombinable):
    """Represent stored text-search vector.

    Used for wrapping either stored ``tsvector`` column or the aggregate of
    such columns.

    """

    def as_sql(self, compiler, connection, function=None, template=None):

        return super(StoredVector, self).as_sql(
            compiler,
            connection,
            function=None,
            template='%(expressions)s')


class OnTheFlyVector(SearchVector, VectorCombinable):
    """Represent on-the-fly calculated text-search vector.

    Used for parsing supplied column in on the fly fashion to ``tsvector``
    and optionally to combine itself with other tsvectors (either on the fly
    ones or stored ones).

    """

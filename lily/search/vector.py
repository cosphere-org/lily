
from django.contrib.postgres.search import (
    SearchVector,
    SearchVectorCombinable,
    CombinedExpression,
)
from django.db import connection
from trans import trans

from .latex.transformer import transform as transform_latex
from .constants import HASHTAG_ESCAPE_SEQUENCE, HASHTAG_PATTERN


def to_tsvector(conf, text, weight=None):
    if text is None:
        return text

    def replace_hashtag(match):

        return "{prefix}{escape_seq}{text}".format(
            prefix=match.group('prefix'),
            escape_seq=HASHTAG_ESCAPE_SEQUENCE,
            text=match.group('text'))

    text = HASHTAG_PATTERN.sub(replace_hashtag, text)
    text = transform_latex(text, conf)

    with connection.cursor() as c:
        # deal with accents
        c.execute(
            "SELECT token FROM ts_debug(%s, %s) WHERE alias != 'blank'",
            [conf, text])
        tokens = [t[0] for t in c.fetchall()]

        escaped_tsvector_part = ''
        if tokens:
            for i, token in enumerate(tokens):
                escaped_token = trans(token.lower())
                if escaped_token != token:
                    escaped_tsvector_part += " '{token}':{position}".format(
                        token=escaped_token,
                        position=i + 1)

        if not weight:
            c.execute("SELECT to_tsvector(%s, %s)", [conf, text])

        else:
            c.execute(
                "SELECT setweight(to_tsvector(%s, %s), %s)",
                [conf, text, weight])

        tsvector = c.fetchone()[0]

        tsvector += escaped_tsvector_part
        return tsvector


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

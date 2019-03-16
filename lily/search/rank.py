
from django.contrib.postgres.search import SearchRank


class Rank(SearchRank):
    """Rank for the calculation of frequency match with 2 normalizations.

    - type 16 normalization - divides the rank by 1 + the logarithm of the
      number of unique words in document
    - type 32 normalization - divides the rank by itself + 1

    """

    def as_sql(self, compiler, connection, function=None, template=None):
        return super(Rank, self).as_sql(
            compiler,
            connection,
            function='ts_rank',
            template='%(function)s(%(expressions)s, 16 | 32)')


class RankCD(SearchRank):
    """Rank for the calculation of harmonic mean distances between tokens.

    It uses Cover Density Rank function and type 4 normalization - divides
    the rank by the mean harmonic distance between extents

    """

    def as_sql(self, compiler, connection, function=None, template=None):
        return super(RankCD, self).as_sql(
            compiler,
            connection,
            function='ts_rank_cd',
            template='%(function)s(%(expressions)s, 4)')

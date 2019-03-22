
from unittest.mock import Mock, call

import search


def test_rank__to_sql(mocker):

    vector, query, compiler, connection = Mock(), Mock(), Mock(), Mock()
    as_sql = mocker.patch('search.rank.SearchRank.as_sql')

    rank = search.Rank(vector, query)
    result = rank.as_sql(compiler, connection)

    assert (
        as_sql.call_args_list ==
        [call(
            compiler,
            connection,
            function='ts_rank',
            template='%(function)s(%(expressions)s, 16 | 32)')])
    assert result == as_sql.return_value


def test_rank_cd__to_sql(mocker):

    vector, query, compiler, connection = Mock(), Mock(), Mock(), Mock()
    as_sql = mocker.patch('search.rank.SearchRank.as_sql')

    rank = search.RankCD(vector, query)
    result = rank.as_sql(compiler, connection)

    assert (
        as_sql.call_args_list ==
        [call(
            compiler,
            connection,
            function='ts_rank_cd',
            template='%(function)s(%(expressions)s, 4)')])
    assert result == as_sql.return_value

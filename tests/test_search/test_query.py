# -*- coding: utf-8 -*-

import pytest
from mock import Mock, call

import search


@pytest.mark.parametrize("value, expected", [

    # case 0 - single word input - no transformation required
    ('hi', 'hi'),

    # case 1 - two words input should be separated by | operator
    ('hi all', 'hi | all'),

    # case 2 - many words input should be separated by | operator
    ('hi all how are you doing', 'hi | all | how | are | you | doing'),

    # case 3 - all punctuation characters are removed and used as split pivotal
    # points
    (
        'hi <>.all||&how&^%%are$@\' you !"|\/ doing',
        'hi | all | how | are | you | doing'
    ),

    # case 4 - hashtags are not removed (hash character is replaced) and
    # presence of hashtags is treated as request for filtering
    # single hashtag
    ('#universe is crazy!', 'hhuniverse & (is | crazy)'),

    # case 5 - hashtags are not removed (hash character is replaced) and
    # presence of hashtags is treated as request for filtering -
    # many hashtags
    (
        '#universe is #crazy and #beautiful',
        'hhuniverse & hhcrazy & hhbeautiful & (is | and)',
    ),

    # case 6 - only hashtags
    (
        '#universe #crazy',
        'hhuniverse & hhcrazy',
    ),

], ids=list(map(str, range(0, 7))))
def test_query__parse_value(value, expected, mocker):
    mocker.patch('search.query.HASHTAG_ESCAPE_SEQUENCE', 'hh')

    q = search.Query('')

    assert expected == q.parse_value(value, 'simple')


@pytest.mark.parametrize("value, language_conf, expected", [

    # case 0 - with auto language detection and latex - pl
    (
        r'witam $$ 2 * x = \\pi $$',
        'polish',
        r'witam | 2 | razy | mnożone | przez | x | równa | się | liczba | pi',
    ),

    # case 1 - with auto language detection and latex - en
    (
        r'hi there $$ 2 * x = \\pi $$',
        'english',
        r'hi | there | 2 | times | x | equals | to | number | pi',
    ),

    # case 2 - with auto language detection and latex - unsupported language
    # (for latex parsing) defaults to English
    (
        r'hi there $$ 2 * x = \\pi $$',
        'french',
        r'hi | there | 2 | times | x | equals | to | number | pi',
    ),

], ids=['0', '1', '2'])
def test_query__get_transformed_value__with_latex(
        value, language_conf, expected, mocker):

    mocker.patch(
        'search.query.detector.detect_db_conf'
    ).return_value = language_conf

    q = search.Query('')

    assert expected == q.parse_value(value, language_conf)


def test_query__to_sql__with_config(mocker):
    mocker.patch(
        'search.query.detector.detect_db_conf'
    ).return_value = 'simple'

    q = search.Query('hi there')
    compiler = Mock(compile=Mock(return_value=['simple', ['a', 'b']]))
    connection = Mock()

    template, params = q.as_sql(compiler, connection)

    assert template == 'to_tsquery(simple::regconfig, %s)'
    assert params == ['a', 'b', 'hi | there']


def test_query__auto_detects_language(mocker):
    mocker.patch(
        'search.query.detector.detect_db_conf'
    ).return_value = 'polish'
    parse_value_mock = mocker.patch.object(
        search.Query, 'parse_value')
    parse_value_mock.return_value = 'witaj | świecie'
    compiler = Mock(compile=Mock(return_value=['polish', []]))

    q = search.Query('witaj świecie!')
    connection = Mock()

    template, params = q.as_sql(compiler, connection)

    assert template == 'to_tsquery(polish::regconfig, %s)'
    assert params == ['witaj | świecie']
    assert (
        parse_value_mock.call_args_list == [call('witaj świecie!', 'polish')])

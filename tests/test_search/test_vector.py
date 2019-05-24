
from unittest.mock import Mock, call

import pytest

import search


def test_stored_vector__to_sql(mocker):

    compiler, connection = Mock(), Mock()
    as_sql = mocker.patch('search.vector.SearchVector.as_sql')

    vector = search.StoredVector('column')
    result = vector.as_sql(compiler, connection)

    assert (
        as_sql.call_args_list ==
        [call(
            compiler,
            connection,
            function=None,
            template='%(expressions)s')])
    assert result == as_sql.return_value


@pytest.mark.parametrize("conf, text, expected", [

    # case 0 - none input, none output
    ('simple', None, None),

    # case 1 - empty string input, empty string output
    ('simple', '', ''),

    # case 2 - single word
    ('simple', 'hello', "'hello':1"),

    # case 3 - many words case
    (
        'simple',
        'hi you how are you?',
        "'hi':1 'you':2,5 'how':3 'are':4",
    ),

    # case 4 - many words case with single hashtag
    (
        'simple',
        'hi #enjoyTheSilence how are you?',
        "'hi':1 '007enjoythesilence':2 'how':3 'are':4 'you':5",
    ),

    # case 5 - many hashtags
    (
        'simple',
        'hi #enjoyTheSilence how are #YouWin #watIsThis?',
        "'hi':1 '007enjoythesilence':2 'how':3 'are':4 '007youwin':5 "
        "'007watisthis':6",
    ),

    # case 6 - transform latex
    (
        'simple',
        r'#enjoyTheSilence $$ \frac{a}{b^2} $$',
        "'007enjoythesilence':1 'fraction':2 'a':3 'divided':4 'by':5 'b':6 "
        "'squared':7",
    ),

    #
    # Language Specific Cases - POLISH
    #
    # case 7 - polish - escape accents
    (
        'polish',
        'część grzegżółek dość Świata',
        "'część':1 'czesc':1 'grzegżółek':2 'grzegzolek':2 'dość':3 "
        "'dosc':3 'świata':4 'swiata':4",
    ),

    # case 8 - polish - escape accents - triangulation
    pytest.param(
        'polish',
        'Pchnąć w tę łódź jeża lub ośm skrzyń fig',
        "'pchnąć':1 'pchnac':1 'w':2 'te':3 'tę':3 'łódź':4 'lodz':4 'jeża':5 "
        "'jeż':5 'jeza':5 'lub':6 'luba':6 'lubić':6 'ośm':7 'osm':7 "
        "'skrzynia':8 'skrzyn':8 'figa':9 'figi':9",
        marks=pytest.mark.xfail(
            reason='it will work again after hunspell integration')
    ),

    # case 9 - many hashtags - polish
    pytest.param(
        'polish',
        'część grzegżółek #dośćŚwiata #wokółNAS słyszałeś',
        "'część':1 'czesc':1 'grzegżółek':2 'grzegzolek':2 '007dośćświata':3 "
        "'007doscswiata':3 '007wokółnas':4 '007wokolnas':4 'slyszales':5 "
        "'słyszeć':5",
        marks=pytest.mark.xfail(
            reason='it will work again after hunspell integration')
    ),

    # case 10 - latex transformation - poi
    pytest.param(
        'polish',
        'rowiązanie to $$ \\sqrt{a ^ 2} $$',
        "'rowiązanie':1 'rowiazanie':1 'ten':2 'to':2 'sqrt':3 'funkcja':4 "
        "'pierwiastek':5 'pierwiastka':5 'kwadratowy':6 'z':7 'a':8 'do':9 "
        "'kwadrat':10",
        marks=pytest.mark.xfail(
            reason='it will work again after hunspell integration')
    ),

], ids=list(map(str, range(0, 11))))
@pytest.mark.django_db
def test_to_tsvector(conf, text, expected, mocker):

    mocker.patch('search.vector.HASHTAG_ESCAPE_SEQUENCE', '007')

    def transform(x):
        if not x:
            return x

        return set(x.split(' '))

    assert transform(search.to_tsvector(conf, text)) == transform(expected)


@pytest.mark.parametrize("v1, v2, v3, expected", [

    # case 0 - single word vectors
    ("'cat':1", "'dog':1", None, "'cat':1 'dog':2"),

    # case 1 - single word vectors with weights
    ("'cat':1B", "'dog':1C", None, "'cat':1B 'dog':2C"),

    # case 2 - many words
    (
        "'cat':1 'whatever':11",
        "'dog':9 'hospital':11 'life':13",
        None,
        "'cat':1 'whatever':11 'dog':20 'hospital':22 'life':24",
    ),

    # case 3 - many words with weights
    (
        "'cat':1B 'whatever':11C",
        "'dog':9 'hospital':11A 'life':13",
        None,
        "'cat':1B 'whatever':11C 'dog':20 'hospital':22A 'life':24",
    ),

    # case 4 - three vectors
    (
        "'cat':1B 'whatever':11C",
        "'dog':9 'hospital':11A 'life':13",
        "'whatever':1B",
        "'cat':1B 'whatever':11C,25B 'dog':20 'hospital':22A 'life':24",
    ),

], ids=list(map(str, range(0, 5))))
@pytest.mark.django_db
def test_concatenate(v1, v2, v3, expected):

    def transform(x):
        if not x:
            return x

        return set(x.split(' '))

    if v3:
        vectors = [v1, v2, v3]

    else:
        vectors = [v1, v2]

    assert (
        transform(search.concatenate_tsvectors(*vectors)) ==
        transform(expected))

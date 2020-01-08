
from unittest.mock import Mock, call

from django.test import TestCase
import pytest

import search
from search import TextVector


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


class TextVectorTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker
        self.mocker.patch('search.vector.HASHTAG_ESCAPE_SEQUENCE', '007')

    def setUp(self):
        self.vector = TextVector()

    def transform_exected(self, expected):

        if expected is None:
            return None

        return {
            k: set([str(e) for e in v])
            for k, v in expected.items()
        }

    def assert_parse(self, conf, text, weight, expected):

        stems = self.vector.parse(conf, text, weight)

        if stems is None:
            assert stems == expected

        else:
            assert stems == self.transform_exected(expected)

    #
    # PARSE - SIMPLE CONF
    #
    def test_parse__none_input_none_output(self):
        self.assert_parse('simple', None, None, {})

    def test_parse__empty_string_input_none_output(self):
        self.assert_parse('simple', '  ', None, {})

    def test_parse__conf_simple__single_word(self):
        self.assert_parse(
            'simple',
            'hello',
            None,
            {
                'hello': (1,),
            })

    def test_parse__conf_simple__many_words(self):
        self.assert_parse(
            'simple',
            'hi you how are you?',
            None,
            {
                'are': (4,),
                'hi': (1,),
                'how': (3,),
                'you': (2, 5),
            })

    def test_parse__conf_simple__with_single_hashtag(self):
        self.assert_parse(
            'simple',
            'hi #enjoyTheSilence how are you?',
            None,
            {
                '007enjoythesilence': (2,),
                'are': (4,),
                'hi': (1,),
                'how': (3,),
                'you': (5,),
            })

    def test_parse__conf_simple__with_many_hashtags(self):
        self.assert_parse(
            'simple',
            'hi #enjoyTheSilence how are #YouWin #watIsThis?',
            None,
            {
                'hi': (1,),
                '007enjoythesilence': (2,),
                'how': (3,),
                'are': (4,),
                '007youwin': (5,),
                '007watisthis': (6,),
            })

    def test_parse__conf_simple__transform_latex(self):
        self.assert_parse(
            'simple',
            r'#enjoyTheSilence $$ \frac{a}{b^2} $$',
            None,
            {
                '007enjoythesilence': (1,),
                'a': (3,),
                'by': (5,), 'b': (6,),
                'divided': (4,),
                'fraction': (2,),
                'squared': (7,),
            })

    #
    # PARSE - POLISH CONF
    #
    def test_parse__conf_polish__escape_accents(self):
        self.assert_parse(
            'polish',
            'część grzegżółek dość Świata',
            None,
            {
                'czesc': (1,),
                'część': (1,),
                'grzegzolek': (2,),
                'grzegżółek': (2,),
                'swiata': (4,),
                'świata': (4,),
            })

    def test_parse__conf_polish__escape_accents_triangulation(
            self):
        self.assert_parse(
            'polish',
            'Pchnąć w tę łódź jeża lub ośm skrzyń fig',
            None,
            {
                'figa': (9,),
                'figi': (9,),
                'jez': (5,),
                'jeza': (5,),
                'jeż': (5,),
                'lodz': (4,),
                'osm': (7,),
                'ośm': (7,),
                'pchnac': (1,),
                'pchnąć': (1,),
                'skrzyn': (8,),
                'skrzynia': (8,),
                'łódź': (4,),
            })

    def test_parse__conf_polish__many_hashtags(self):
        self.assert_parse(
            'polish',
            'część grzegżółek #dośćŚwiata #wokółNAS słyszałeś',
            None,
            {
                '007doscswiata': (3,),
                '007dośćświata': (3,),
                '007wokolnas': (4,),
                '007wokółnas': (4,),
                'czesc': (1,),
                'część': (1,),
                'grzegzolek': (2,),
                'grzegżółek': (2,),
                'słyszeć': (5,),
                'slyszec': (5,),
                'slyszales': (5,),
            })

    def test_parse__conf_polish__latex_transformation(self):
        self.assert_parse(
            'polish',
            'rozwiązanie to $$ \\sqrt{a ^ 2} $$',
            None,
            {
                'funkcja': (4,),
                'kwadrat': (10,),
                'kwadratowy': (6,),
                'pierwiastek': (5,),
                'pierwiastka': (5,),
                'rozwiazanie': (1,),
                'rozwiązanie': (1,),
                'rozwiazac': (1,),
                'rozwiązać': (1,),
                'sqrt': (3,),
            })

    def test_parse__conf_polish__with_weight(self):
        self.assert_parse(
            'polish',
            'dzień dobry świecie',
            'B',
            {
                'dobry': ('2B',),
                'dzien': ('1B',),
                'dzień': ('1B',),
                'swiecie': ('3B',),
                'świecie': ('3B',),
            })

    def test_parse__conf_polish__with_commas_and_dots(self):
        self.assert_parse(
            'polish',
            'rozwiązanie, to. jest, ok, ale, inne, jest prostsze.',
            None,
            {
                'prostszy': (8,),
                'rozwiazac': (1,),
                'rozwiazanie': (1,),
                'rozwiązanie': (1,),
                'rozwiązać': (1,),
            })

    def test_parse__conf_polish__with_other_extra_characters(self):
        self.assert_parse(
            'polish',
            'rozwiązanie;+- to%^& jest, ok, ale, san-jose, jest prostsze.',
            None,
            {
                'prostszy': (10,),
                'rozwiazac': (1,),
                'rozwiazanie': (1,),
                'rozwiązanie': (1,),
                'rozwiązać': (1,),
                'san-jose': (6,),
                'san': (7,),
                'jose': (8,),
            })

    def test_parse__conf_polish__multiple_positions(self):
        self.assert_parse(
            'polish',
            'adam adam ma kota kot ma adama',
            None,
            {
                'adam': set([2, 1]),
                'adama': set([7]),
                'kot': set([4, 5]),
                'kota': set([4, 5]),
            })

    def test_parse__conf_polish__broken_no_stem_words_positions(
            self):
        self.assert_parse(
            'polish',
            'zjezdzalnia brakuje polskich znakow',
            None,
            {
                'brakowac': (2,),
                'brakować': (2,),
                'brakuje': (2,),
                'polski': (3,),
                'zjezdzalnia': (1,),
                'znakow': (4,),
            })

    def test_parse__conf_polish__stop_words_removed(self):
        self.assert_parse(
            'polish',
            'i lub ale to ta te',
            None,
            {})

    def test_parse__conf_polish__not_have_to_contain_letters(self):
        self.assert_parse(
            'polish',
            '123 14 16 19 wynik to 190',
            None,
            {
                '123': (1,),
                '14': (2,),
                '16': (3,),
                '19': (4,),
                '190': (7,),
                'wynik': (5,)
            })

    #
    # PARSE - ENGLISH CONF
    #
    def test_parse__conf_english__many_hashtags(self):
        self.assert_parse(
            'english',
            'hello #around #theWorld',
            None,
            {
                'hello': (1,),
                '007around': (2,),
                '007theworld': (3,),
            })

    def test_parse__conf_english__latex_transformation(self):
        self.assert_parse(
            'english',
            'hello $$ \\frac{a}{b} $$',
            None,
            {
                'b': (6,),
                'divid': (4,),
                'fraction': (2,),
                'hello': (1,),
            })

    def test_parse__conf_english__with_weight(self):
        self.assert_parse(
            'english',
            'hello world',
            'A',
            {
                'hello': ('1A',),
                'world': ('2A',),
            })

    def test_parse__conf_english__with_commas_and_dots(self):
        self.assert_parse(
            'english',
            'hello, world. What, is. happening',
            None,
            {
                'happen': (5,),
                'hello': (1,),
                'world': (2,),
            })

    def test_parse__conf_english__with_other_extra_characters(
            self):
        self.assert_parse(
            'english',
            'hello;;*( world; What^& is. happening in san-jose',
            None,
            {
                'happen': (5,),
                'hello': (1,),
                'world': (2,),
                'jose': (9,),
                'san': (8,),
                'san-jos': (7,),
            })

    def test_parse__conf_english__multiple_positions(self):
        self.assert_parse(
            'english',
            'hello hello world hello what world?',
            None,
            {
                'hello': (4, 2, 1),
                'world': (6, 3),
            })

    def test_parse__conf_english__broken_no_stem_words_positions(
            self):
        self.assert_parse(
            'english',
            'helloooo worrld',
            None,
            {
                'helloooo': (1,),
                'worrld': (2,),
            })

    def test_parse__conf_english__stop_words_removed(self):
        self.assert_parse(
            'english',
            'who you are how is now?',
            None,
            {})

    def test_parse__conf_english__not_have_to_contain_letters(
            self):
        self.assert_parse(
            'english',
            'the day is 1893 and it 19 and 56',
            None,
            {
                '1893': (4,),
                '19': (7,),
                '56': (9,),
                'day': (2,),
            })

    #
    # PARSE_TO_LIST
    #
    def test_parse_to_list__makes_the_right_calls(self):

        parse = self.mocker.patch.object(TextVector, 'parse')
        parse.return_value = {
            'dzień': set(['1', '3']),
            'świecie': set(['2']),
        }
        assert self.vector.parse_to_list(
            'polish',
            'dzień dobry świecie',
            None
        ) == ['dzień', 'świecie']
        assert parse.call_args_list == [
            call('polish', 'dzień dobry świecie', None)
        ]

    #
    # PARSE_TO_TSVECTOR
    #
    def test_parse_to_tsvector__makes_the_right_calls(self):

        parse = self.mocker.patch.object(TextVector, 'parse')
        parse.return_value = {
            'dzień': set(['1']),
            'świecie': set(['2']),
        }
        assert self.vector.parse_to_tsvector(
            'polish',
            'dzień dobry świecie',
            None
        ) == "'dzień':1 'świecie':2"
        assert parse.call_args_list == [
            call('polish', 'dzień dobry świecie', None)
        ]

    #
    # TRANSFORM_HASHTAGS
    #
    def test_transform_hashtags(self):

        # -- single hashtag only
        assert self.vector.transform_hashtags('#hi') == '007hi'

        # -- single hashtag - at the beginning
        assert self.vector.transform_hashtags('#hi world') == '007hi world'

        # -- single hashtag - at the end
        assert self.vector.transform_hashtags('world #hi') == 'world 007hi'

        # -- single hashtag - in the middle
        assert self.vector.transform_hashtags(
            'world #hi you') == 'world 007hi you'

        # -- many hashtags
        assert self.vector.transform_hashtags(
            '#hi #what is not #this but #that'
        ) == '007hi 007what is not 007this but 007that'

        # -- unicode hashtags
        assert self.vector.transform_hashtags(
            '#ówdzie #późno is not #this but #that'
        ) == '007ówdzie 007późno is not 007this but 007that'

    #
    # TRANSFORM_LATEX
    #
    def test_transform_latex__conf_english(self):

        # -- single latex only
        assert self.vector.transform_latex(
            'english', '$$ \\frac{a}{b} $$'
        ) == 'fraction a divided by b'

        # -- single latex - at the beginning
        assert self.vector.transform_latex(
            'english', '$$ \\frac{a}{b} $$ and else'
        ) == 'fraction a divided by b and else'

        # -- single latex - at the end
        assert self.vector.transform_latex(
            'english', 'what is $$ \\frac{a}{b} $$'
        ) == 'what is fraction a divided by b'

        # -- single latex - in the middle
        assert self.vector.transform_latex(
            'english', 'what is $$ \\frac{a}{b} $$ and final'
        ) == 'what is fraction a divided by b and final'

        # -- many latex expressions
        assert self.vector.transform_latex(
            'english',
            'what is $$ \\frac{a}{b} $$ and $$ a $$ '
            'what $$ \\sqrt{x} $$'
        ) == (
            'what is fraction a divided by b and a what sqrt square root '
            'function of x'
        )

    def test_transform_latex__conf_polish(self):

        # -- single latex only
        assert self.vector.transform_latex(
            'polish', '$$ \\frac{a}{b} $$'
        ) == 'ułamek a dzielone przez b'

        # -- single latex - at the beginning
        assert self.vector.transform_latex(
            'polish', '$$ \\frac{a}{b} $$ i inne'
        ) == 'ułamek a dzielone przez b i inne'

        # -- single latex - at the end
        assert self.vector.transform_latex(
            'polish', 'czym jest $$ \\frac{a}{b} $$'
        ) == 'czym jest ułamek a dzielone przez b'

        # -- single latex - in the middle
        assert self.vector.transform_latex(
            'polish', 'czym jest $$ \\frac{a}{b} $$ i na koniec'
        ) == 'czym jest ułamek a dzielone przez b i na koniec'

        # -- many latex expressions
        assert self.vector.transform_latex(
            'polish',
            'czym jest $$ \\frac{a}{b} $$ oraz $$ a $$ '
            'czym $$ \\sqrt{x} $$'
        ) == (
            'czym jest ułamek a dzielone przez b oraz a czym sqrt funkcja '
            'pierwiastek kwadratowy z x'
        )

    #
    # TOKENIZE
    #
    def test_tokenize(self):

        # -- empty case
        assert self.vector.tokenize('simple', '') == []

        # -- conf simple
        assert self.vector.tokenize('simple', 'hi there how are you') == [
            ('hi', 1), ('there', 2), ('how', 3), ('are', 4), ('you', 5)
        ]

        # -- conf english
        assert self.vector.tokenize('english', 'hi there how are you') == [
            ('hi', 1), ('there', 2), ('how', 3), ('are', 4), ('you', 5)
        ]

        # -- conf polish
        assert self.vector.tokenize(
            'polish',
            'cześć wam jak się czujecie?'
        ) == [
            ('cześć', 1), ('czujecie', 5)
        ]

        # -- extra characters are removed
        assert self.vector.tokenize('simple', 'hi;; there+=& how are you') == [
            ('hi', 1), ('there', 2), ('how', 3), ('are', 4), ('you', 5)
        ]

    #
    # AUGUMENT_WITH_UNACCENTS
    #
    def test_augument_with_unaccents__no_accents(self):

        assert self.vector.augument_with_unaccents(
            'polish',
            None,
            {'mam': set(['3'])},
            [('hej', 1), ('jak', 2), ('macie', 3)]
        ) == {
            'mam': set(['3']),
        }

    def test_augument_with_unaccents__tokens_only(self):

        assert self.vector.augument_with_unaccents(
            'polish',
            None,
            {},
            [('cześć', 1), ('jak', 2), ('świecie', 3)]
        ) == {
            'czesc': set(['1']),
            'swiecie': set(['3']),
        }

    def test_augument_with_unaccents__stems_only(self):

        assert self.vector.augument_with_unaccents(
            'polish',
            None,
            {
                'cześć': set(['1']),
                'jak': set(['2']),
                'świecie': set(['3', '4']),
            },
            []
        ) == {
            'czesc': set(['1']),
            'cześć': set(['1']),
            'jak': set(['2']),
            'świecie': set(['3', '4']),
            'swiecie': set(['3', '4']),
        }

    def test_augument_with_unaccents__stems_and_tokens(self):

        assert self.vector.augument_with_unaccents(
            'polish',
            None,
            {'cześć': set(['1']), 'czesc': set(['2'])},
            [('cześć', 1), ('jak', 2), ('macie', 3)]
        ) == {
            'czesc': set(['1', '2']),
            'cześć': set(['1']),
        }

    #
    # AUGUMENT_WITH_STEMS
    #
    def test_augument_with_stems__simple_conf(self):

        assert self.vector.augument_with_stems(
            'simple',
            'hello there',
            None,
            {
                'already': set(['1', '5']),
            },
            [('will', 1), ('be', 2), ('ignored', 3)]
        ) == {
            'already': set(['1', '5']),
            'hello': set(['1']),
            'there': set(['2']),
        }

    def test_augument_with_stems__polish_conf(self):

        assert self.vector.augument_with_stems(
            'polish',
            'cześć wam zdobyliście wszystkie zasługi?',
            None,
            {},
            [
                ('cześć', 1),
                ('zdobyliście', 3),
                ('wszystkie', 4),
                ('zasługi', 5),
            ]
        ) == {
            'cześć': set(['1']),
            'wszystkie': set(['4']),
            'zasługa': set(['5']),
            'zdobyć': set(['3']),
        }

    def test_augument_with_stems__english_conf(self):

        assert self.vector.augument_with_stems(
            'english',
            'hey there did you gained everything?',
            None,
            {},
            [('will', 1), ('be', 2), ('ignored', 3)]
        ) == {
            'everyth': set(['6']),
            'gain': set(['5']),
            'hey': set(['1']),
        }


#
# HELPERS
#
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

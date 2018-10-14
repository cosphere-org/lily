
from unittest import TestCase

import pytest

from lily.base.utils import normalize_indentation, Timer


def s(*args):
    return '\n'.join(args)


@pytest.mark.parametrize(
    'text, min_indent, expected',
    [
        # -- empty to empty
        ('', 0, ''),

        # -- single liner
        (
            '''
            hello world
            ''',
            0,
            s('hello world'),
        ),

        # -- trim beginning and ending
        (
            '''

            hello world


            ''',
            0,
            s('hello world'),
        ),

        # -- multi line
        (
            '''
            hello world
            or not hello
            ''',
            0,
            s(
                'hello world',
                'or not hello',
            ),
        ),

        # -- multi line - varying indent
        (
            '''
            hello world
                or not hello
                  what
            ''',
            0,
            s(
                'hello world',
                '    or not hello',
                '      what'
            ),
        ),

        # -- multi line - non zero min_indent
        (
            '''
            hello world
                or not hello
                  what
            ''',
            2,
            s(
                '  hello world',
                '      or not hello',
                '        what'
            ),
        ),

        # -- multi line - empty lines between
        (
            '''
            hello world


            what
            ''',
            0,
            s(
                'hello world',
                '',
                '',
                'what'
            ),
        ),

    ])
def test_normalize_indentation(text, min_indent, expected):
    assert normalize_indentation(text, min_indent) == expected


class TimerTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker):
        self.mocker = mocker

    #
    # ELASED
    #
    def test_elapsed(self):

        M = 60  # noqa
        H = 3600  # noqa

        self.mocker.patch('lily.base.utils.time').side_effect = [
            # -- 1st
            134,
            134 + 11.012,
            # -- 2nd
            146,
            146 + (3 * M + 17.189000),
            # -- 3rd
            189,
            189 + (2 * H + 7 * M + 17),
        ]

        with Timer() as t:
            assert t.elapsed == '00:00:11.012'

        with Timer() as t:
            assert t.elapsed == '00:03:17.189'

        with Timer() as t:
            assert t.elapsed == '02:07:17.000'

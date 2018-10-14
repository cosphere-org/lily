
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
    def test_elased(self):

        self.mocker.patch('lily.base.utils.time').side_effect = [134, 145]

        with Timer() as t:
            assert t.elapsed == 11

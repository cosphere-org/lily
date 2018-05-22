# -*- coding: utf-8 -*-

import pytest

from lily.docs.renderers.angular.utils import (
    to_camelcase,
    normalize_indentation,
)


@pytest.mark.parametrize(
    'name, expected', [
        # -- empty to empty
        ('', ''),

        # -- single letter capital to same
        ('A', 'A'),

        # -- camel to camel
        ('Abc', 'Abc'),

        # -- camel to camel
        ('Abc', 'Abc'),

        # -- all UPPER to camel
        ('ABCD', 'Abcd'),

        # -- all lower to camel
        ('abcd', 'Abcd'),

        # -- underscore case
        ('ab_cde_f', 'AbCdeF'),

        # -- mixed case
        ('ab_CDe_f', 'AbCdeF'),

    ])
def test_to_camelcase(name, expected):

    assert to_camelcase(name) == expected


@pytest.mark.parametrize(
    'name, expected', [
        # -- empty to empty
        ('', ''),

        # -- single letter capital to same
        ('A', 'a'),

        # -- all lower to camel
        ('ABcd', 'abcd'),

        # -- underscore case
        ('ab_cde_f', 'abCdeF'),

        # -- mixed case
        ('ab_CDe_f', 'abCdeF'),
    ])
def test_to_camelcase__first_lower(name, expected):

    assert to_camelcase(name, first_lower=True) == expected


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

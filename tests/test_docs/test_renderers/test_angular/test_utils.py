
import pytest

from lily.docs.renderers.angular.utils import to_camelcase


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
        ('ab_CDe_f', 'AbCDeF'),

        # -- camel case stays camel case
        ('AgeChoice', 'AgeChoice'),

        # -- all upper is lower first
        ('AGE_CHOICE', 'AgeChoice'),
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
        ('ABcd', 'aBcd'),

        # -- underscore case
        ('ab_cde_f', 'abCdeF'),

        # -- mixed case
        ('ab_CDe_f', 'abCDeF'),
    ])
def test_to_camelcase__first_lower(name, expected):

    assert to_camelcase(name, first_lower=True) == expected

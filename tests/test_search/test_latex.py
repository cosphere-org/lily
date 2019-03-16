
import re
import random

import pytest

from search.latex import transformer
from tests.test_search import LATEX_CASES


def _normalize(x):
    x = re.sub(r'\s+', ' ', x)
    return x.strip()


def _normalize_desc(x):
    x = re.sub(r'\s+', '_', x)
    return re.sub(r'\W+', '', x)


def _select_cases(cases):

    def _select_case(c):
        priority_test_run = (
            any(map(lambda c: c.get('run_test', False), cases)))
        return (
            not priority_test_run or
            (priority_test_run and c.get('run_test', False)))

    return [c for c in cases if _select_case(c)]


@pytest.mark.parametrize(
    "text, english_expected, polish_expected",
    [[
        c['text'],
        c['english_expected'],
        c['polish_expected']]
     for c in _select_cases(LATEX_CASES)],
    ids=[_normalize_desc(c['description'])
         for c in _select_cases(LATEX_CASES)])
def test_transform(text, english_expected, polish_expected, mocker):

    mocker.patch('search.latex.transformer.MAX_ITERATIONS_COUNT', 3)

    assert (
        _normalize(transformer.transform(text, 'english')) ==
        _normalize(english_expected))

    assert (
        _normalize(transformer.transform(text, 'polish')) ==
        _normalize(polish_expected))

    # here we can randomize all other languages to make sure that they
    # always default to english is not supported
    other_languages = [
        'danish', 'dutch', 'finnish', 'french', 'german', 'hungarian',
        'italian', 'norwegian', 'portuguese', 'romanian', 'russian',
        'simple', 'spanish', 'swedish', 'turkish',
    ]
    random_language = random.choice(other_languages)
    assert (
        _normalize(transformer.transform(text, random_language)) ==
        _normalize(english_expected))

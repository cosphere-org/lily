# -*- coding: utf-8 -*-

from mock import call

from search.detector import get_search_conf_language


def test_get_search_conf_language__returns_simple_detect_result(mocker):
    simple_detect_mock = mocker.patch(
        'search.detector.detector.detectlanguage.simple_detect')
    simple_detect_mock.side_effect = ['es', 'en', 'eo']

    # 1st call with spanish
    result = get_search_conf_language('hola Xavier!')

    assert result == 'spanish'

    # 2nd call with english
    result = get_search_conf_language('hello J!')

    assert result == 'english'

    # 3rd call with Esperanto
    result = get_search_conf_language('Saluton PJ!')

    assert result == 'simple'

    # make sure that calls where correctly invoked
    assert (
        simple_detect_mock.call_args_list ==
        [call('hola Xavier!'), call('hello J!'), call('Saluton PJ!')])


def test_get_search_conf_language__returned_abbreviation_is_unknown(mocker):
    simple_detect_mock = mocker.patch(
        'search.detector.detector.detectlanguage.simple_detect')
    simple_detect_mock.return_value = 'ff'

    # 1st call with spanish
    result = get_search_conf_language('whatever')

    assert result == 'simple'
    assert simple_detect_mock.call_count == 1


def test_get_search_conf_language__external_module_raises_index_error(mocker):
    simple_detect_mock = mocker.patch(
        'search.detector.detector.detectlanguage.simple_detect')
    simple_detect_mock.side_effect = IndexError

    result = get_search_conf_language('hello you!')

    assert result == 'simple'
    assert simple_detect_mock.call_count == 1


def test_get_search_conf_language__min_detection_length(mocker):
    simple_detect_mock = mocker.patch(
        'search.detector.detector.detectlanguage.simple_detect')

    result = get_search_conf_language('wat!')

    assert result == 'simple'
    assert simple_detect_mock.call_count == 0

# -*- coding: utf-8 -*-

from django.test import TestCase
from mock import Mock
import pytest

from lily.base.name import (
    to_past,
    BaseVerb,
    ConstantName,
    Create,
    Update,
    Upsert,
    Read,
    List,
    Delete,
    Execute,
)
from lily.base.events import EventFactory


class ConstantNameTestCase(TestCase):

    def test_render_command_name(self):
        c = ConstantName('hi  there')

        assert c.render_command_name() == 'HI_THERE'

    def test_render_event_name(self):
        c = ConstantName('hi  there')

        assert c.render_event_name(
            Mock(), Mock(event='hello yo')) == 'HELLO_YO'


class VerbsTestCase(TestCase):

    def test_accepts_string_noun_or_model(self):

        card = Mock(_meta=Mock(model_name='Card'))
        user = Mock(_meta=Mock(model_name='User'))

        class GreetVerb(BaseVerb):
            verb = 'greet'

        # -- noun is the string
        v = GreetVerb('laundry')

        assert v.render_command_name() == 'GREET_LAUNDRY'

        # -- noun is a model
        v = GreetVerb(user)

        assert v.render_command_name() == 'GREET_USER'

        # -- noun is a model - triangulation
        v = GreetVerb(card)

        assert v.render_command_name() == 'GREET_CARD'

    def test_render_event_name__wrong_finalizer(self):

        # -- Success instead of Created
        try:
            assert Create('Car').render_event_name(
                Mock(), EventFactory.Success())

        except EventFactory.BrokenRequest as e:
            assert e.event == (
                'INVALID_FINALIZER_USED_FOR_SPECIFIC_COMMAND_DETECTED')

        # -- Updated instead of Deleted
        try:
            assert Delete('Car').render_event_name(
                Mock(), EventFactory.Updated())

        except EventFactory.BrokenRequest as e:
            assert e.event == (
                'INVALID_FINALIZER_USED_FOR_SPECIFIC_COMMAND_DETECTED')


class ExecuteTestCase(TestCase):

    def test_accepts_custom_verb(self):

        assert Execute('Get', 'Car').render_command_name() == 'GET_CAR'
        assert Execute('Get', 'Car').render_event_name() == 'CAR_GOT'

    def test_render_event_name__wrong_finalizer(self):

        try:
            assert Execute('Get', 'Car').render_event_name(
                Mock(), EventFactory.Success())

        except EventFactory.BrokenRequest as e:
            assert e.event == (
                'INVALID_FINALIZER_USED_FOR_SPECIFIC_COMMAND_DETECTED')


class UpsertTestCase(TestCase):

    def test_render_event_name__accepts_many_finalizers(self):

        assert Upsert('Car').render_event_name(
            Mock(), EventFactory.Created()) == 'CAR_CREATED'

        assert Upsert('Box').render_event_name(
            Mock(), EventFactory.Updated()) == 'BOX_UPDATED'


@pytest.mark.parametrize(
    'verb, expected_command, expected_event', [
        (Create('home'), 'CREATE_HOME', 'HOME_CREATED'),
        (Update('candy'), 'UPDATE_CANDY', 'CANDY_UPDATED'),
        (Upsert('home'), 'UPSERT_HOME', 'HOME_CREATED'),
        (Read('bicycle'), 'READ_BICYCLE', 'BICYCLE_READ'),
        (List('box'), 'LIST_BOX', 'BOX_LISTED'),
        (Delete('home'), 'DELETE_HOME', 'HOME_DELETED'),
        (Execute('buy', 'home'), 'BUY_HOME', 'HOME_BOUGHT'),
    ])
def test_verbs(verb, expected_command, expected_event):

    assert verb.render_command_name() == expected_command

    e = verb.finalizers[0]()
    assert verb.render_event_name(Mock(), e) == expected_event


@pytest.mark.parametrize(
    'verb, expected', [
        # -- irregular
        ('come', 'came'),
        ('pay', 'paid'),

        # -- single form
        ('read', 'read'),

        # -- regular
        ('list', 'listed'),

        # -- finishes with `e`
        ('create', 'created'),
        ('update', 'updated'),
        ('delete', 'deleted'),
        ('execute', 'executed'),

        # -- finishes with `y`
        ('execute', 'executed'),

        # -- with double consonant
        ('stop', 'stopped'),

        # -- exceptions
        ('refer', 'referred'),

        # -- NO double consonant
        ('visit', 'visited'),
    ])
def test_to_past(verb, expected):

    assert to_past(verb) == expected


@pytest.mark.parametrize(
    'phrase, expected_command, expected_event', [
        (
            Create('card').after.Delete('user'),
            'CREATE_CARD_AFTER_DELETE_USER',
            'CARD_CREATED_AFTER_USER_DELETED',
        ),

        (
            List('payment').after.Upsert('card'),
            'LIST_PAYMENT_AFTER_UPSERT_CARD',
            'PAYMENT_LISTED_AFTER_CARD_UPSERTED',
        ),
    ])
def test_cause_and_effect(phrase, expected_command, expected_event):

    assert phrase.render_command_name() == expected_command

    e = phrase.effect.finalizers[0]()
    assert phrase.render_event_name(Mock(), e) == expected_event

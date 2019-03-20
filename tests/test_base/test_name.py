
from unittest.mock import Mock

from django.test import TestCase
import pytest

from lily.base.name import (
    to_past,
    to_plural,
    BaseVerb,
    ConstantName,
    Execute,
    # -- CRUD
    Create,
    Read,
    Update,
    Delete,
    # -- BULK CRUD
    BulkCreate,
    BulkRead,
    BulkUpdate,
    BulkDelete,
    # -- CONDITIONAL CRUD
    CreateOrUpdate,
    CreateOrRead,
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

        # -- Success Executed of Created
        try:
            assert Create('Car').render_event_name(
                Mock(), EventFactory.Executed())

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
                Mock(), EventFactory.Created())

        except EventFactory.BrokenRequest as e:
            assert e.event == (
                'INVALID_FINALIZER_USED_FOR_SPECIFIC_COMMAND_DETECTED')


class CreateOrUpdateTestCase(TestCase):

    def test_render_event_name__accepts_many_finalizers(self):

        assert CreateOrUpdate('Car').render_event_name(
            Mock(), EventFactory.Created()) == 'CAR_CREATED'

        assert CreateOrUpdate('Box').render_event_name(
            Mock(), EventFactory.Updated()) == 'BOX_UPDATED'


class CreateOrReadTestCase(TestCase):

    def test_render_event_name__accepts_many_finalizers(self):

        assert CreateOrRead('Car').render_event_name(
            Mock(), EventFactory.Created()) == 'CAR_CREATED'

        assert CreateOrRead('Box').render_event_name(
            Mock(), EventFactory.Read()) == 'BOX_READ'


class BulkReadTestCase(TestCase):

    def test_applies_pluralization(self):

        user = Mock(_meta=Mock(model_name='User'))

        # -- render_command_name
        assert BulkRead('Car').render_command_name() == 'BULK_READ_CARS'

        assert BulkRead('boxes').render_command_name() == 'BULK_READ_BOXES'

        assert BulkRead(user).render_command_name() == 'BULK_READ_USERS'

        # -- render_event_name
        assert BulkRead('Car').render_event_name(
            Mock(), EventFactory.BulkRead()) == 'CARS_BULK_READ'

        assert BulkRead('boxes').render_event_name(
            Mock(), EventFactory.BulkRead()) == 'BOXES_BULK_READ'

        assert BulkRead(user).render_event_name(
            Mock(), EventFactory.BulkRead()) == 'USERS_BULK_READ'


@pytest.mark.parametrize(
    'verb, expected_command, expected_event', [
        # -- CRUD
        (Create('home'), 'CREATE_HOME', 'HOME_CREATED'),
        (Update('candy'), 'UPDATE_CANDY', 'CANDY_UPDATED'),
        (Read('bicycle'), 'READ_BICYCLE', 'BICYCLE_READ'),
        (Delete('home'), 'DELETE_HOME', 'HOME_DELETED'),
        # -- BULK CRUD
        (BulkCreate('box'), 'BULK_CREATE_BOXES', 'BOXES_BULK_CREATED'),
        (BulkRead('box'), 'BULK_READ_BOXES', 'BOXES_BULK_READ'),
        (BulkUpdate('lock'), 'BULK_UPDATE_LOCKS', 'LOCKS_BULK_UPDATED'),
        (BulkDelete('cat'), 'BULK_DELETE_CATS', 'CATS_BULK_DELETED'),
        (Execute('buy', 'home'), 'BUY_HOME', 'HOME_BOUGHT'),
        (CreateOrUpdate('home'), 'CREATE_OR_UPDATE_HOME', 'HOME_CREATED'),
        (CreateOrRead('home'), 'READ_OR_CREATE_HOME', 'HOME_CREATED'),
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
    'noun, expected', [
        # -- regular
        ('apple', 'apples'),
        ('card', 'cards'),

        # -- irregular
        ('wolf', 'wolves'),

        # -- plural stay plural
        ('paths', 'paths'),
        ('wolves', 'wolves'),
    ])
def test_to_plural(noun, expected):

    assert to_plural(noun) == expected


@pytest.mark.parametrize(
    'phrase, expected_command, expected_event', [
        (
            Create('card').after.Delete('user'),
            'CREATE_CARD_AFTER_DELETE_USER',
            'CARD_CREATED_AFTER_USER_DELETED',
        ),

        (
            BulkRead('payment').after.CreateOrUpdate('card'),
            'BULK_READ_PAYMENTS_AFTER_CREATE_OR_UPDATE_CARD',
            'PAYMENTS_BULK_READ_AFTER_CARD_CREATE_OR_UPDATED',
        ),
    ])
def test_cause_and_effect(phrase, expected_command, expected_event):

    assert phrase.render_command_name() == expected_command

    e = phrase.effect.finalizers[0]()
    assert phrase.render_event_name(Mock(), e) == expected_event

# -*- coding: utf-8 -*-

from mock import Mock

from base.events import cause_effect


def test_cause_effect():

    card = Mock(_meta=Mock(model_name='Card'))
    user = Mock(_meta=Mock(model_name='User'))

    assert cause_effect(
        on_created=user, created=card) == 'ON_USER_CREATED_CARD_CREATED'

    assert cause_effect(
        on_updated=user, created=card) == 'ON_USER_UPDATED_CARD_CREATED'

    assert cause_effect(
        on_removed=card, created=user) == 'ON_CARD_REMOVED_USER_CREATED'

    assert cause_effect(
        on_removed=card, removed=card) == 'ON_CARD_REMOVED_CARD_REMOVED'

    assert cause_effect(
        on_created=card, updated=user) == 'ON_CARD_CREATED_USER_UPDATED'

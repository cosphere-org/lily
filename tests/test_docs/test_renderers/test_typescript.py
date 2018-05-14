# -*- coding: utf-8 -*-

from unittest import TestCase

import pytest
# from mock import Mock

# from lily.base import serializers, parsers
# from lily.docs.renderers.typescript import CommandsRenderer
# from lily.docs.renderers.base import BaseRenderer
from lily.docs.renderers.typescript import to_camelcase


class CommandsRendererTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def test_render(self):
        pass

    # def serialize_name(self):
    #     if self.type == SERIALIZER_TYPES.RESPONSE:
    #         return 'Response'

    #     elif self.type == SERIALIZER_TYPES.REQUEST_BODY:
    #         return 'RequestBody'

    #     elif self.type == SERIALIZER_TYPES.REQUEST_QUERY:
    #         return 'RequestQuery'

    #
    # remove_enums_duplicates
    #
    # def test_remove_enums_duplicates(self):

    #     schema = SchemaRenderer(HumanSerializer).render()
    #     schema.enums = [
    #         Enum('kind', ['1', '2']),

    #         # -- duplicated name, same values
    #         Enum('kind', ['1', '2']),

    #         # -- duplicated name, same values - different order
    #         Enum('kind', ['2', '1']),

    #         # -- duplicated name, different values
    #         Enum('kind', ['1', '2', '3']),

    #         # -- other duplicated name, different values
    #         Enum('kind', ['1', 'a']),
    #     ]

    #     enums = schema.remove_enums_duplicates()

    #     assert len(enums) == 3
    #     enums_index = {enum.name: enum.values for enum in enums}
    #     assert enums_index['ResponseKind'] == ['1', '2']
    #     assert enums_index['ResponseKind1'] == ['1', '2', '3']
    #     assert enums_index['ResponseKind2'] == ['1', 'a']


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

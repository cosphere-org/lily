# -*- coding: utf-8 -*-

from django.test import TestCase

from lily.base.access import Access


class AccessTestCase(TestCase):

    def test_defaults(self):

        a = Access()

        assert a.access_list is None
        assert a.is_private is False

    def test_arguments_are_saved(self):

        a = Access(
            access_list=['SUPER_USER'],
            is_private=True)

        assert a.access_list == ['SUPER_USER']
        assert a.is_private is True

    def test_serialize(self):

        a = Access(
            access_list=['SUPER_USER'],
            is_private=True)

        assert a.serialize() == {
            'is_private': True,
            'access_list': ['SUPER_USER'],
        }

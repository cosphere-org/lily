# -*- coding: utf-8 -*-

from django.test import TestCase
import pytest

from lily.base.meta import Meta, Domain


class MetaTestCase(TestCase):

    def test_required_fields(self):
        # -- missing title
        with pytest.raises(TypeError):
            Meta(domain=Domain(id='d', name='d'))

        # -- missing domain
        with pytest.raises(TypeError):
            Meta(title='hi there')

    def test_arguments_are_saved(self):

        m = Meta(
            title='hi there',
            description='this is it',
            domain=Domain(id='d', name='d'))

        assert m.title == 'hi there'
        assert m.description == 'this is it'
        assert m.domain == Domain(id='d', name='d')

    def test_serialize(self):

        m = Meta(
            title='hi there',
            description='this is it',
            domain=Domain(id='a', name='aaa'))

        assert m.serialize() == {
            'title': 'hi there',
            'description': 'this is it',
            'domain': 'aaa',
        }


class AccessTestCase(TestCase):

    def test_required_fields(self):
        # -- missing id
        with pytest.raises(TypeError):
            Domain(name='hi')

        # -- missing name
        with pytest.raises(TypeError):
            Domain(id='hi')

    def test_arguments_are_saved(self):

        d = Domain(id='cards', name='Cards Management')

        assert d.id == 'cards'
        assert d.name == 'Cards Management'

    def test_serialize(self):

        d = Domain(
            id='super',
            name='Super Management')

        assert d.serialize() == {
            'id': 'super',
            'name': 'Super Management',
        }

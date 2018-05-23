# -*- coding: utf-8 -*-

from django.test import TestCase

from lily.docs.renderers.angular.domain import Path, Domain


class PathTestCase(TestCase):

    def test_join(self):
        assert Path('/home/jake').join('photo.png') == '/home/jake/photo.png'


class DomainTestCase(TestCase):

    def test_attributes(self):

        d = Domain('cards', 'Cards Management')

        assert d.id == 'cards'
        assert d.name == 'Cards Management'
        assert d.camel_id == 'Cards'

    def test_path(self):

        path = Domain('cards', 'Cards Management').path

        assert isinstance(path, Path)
        assert path.base_path == '/src/domains/cards'

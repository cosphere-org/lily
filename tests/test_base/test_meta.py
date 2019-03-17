
from django.test import TestCase
import pytest

from lily.base.meta import Meta, MetaSerializer, Domain, DomainSerializer
from lily.base.events import EventFactory


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


class MetaSerializerTestCase(TestCase):

    def test_serialization(self):

        m = Meta(
            title='hi there',
            description='this is it',
            domain=Domain(id='a', name='aaa'))

        assert MetaSerializer(m).data == {
            '@type': 'meta',
            'title': 'hi there',
            'description': 'this is it',
            'domain': {
                '@type': 'domain',
                'id': 'a',
                'name': 'aaa',
            },
        }


class DomainTestCase(TestCase):

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

    def test_invalid_id(self):

        with pytest.raises(EventFactory.BrokenRequest) as e:
            Domain(id='cards manager', name='...')

        assert e.value.event == 'BROKEN_ARGS_DETECTED'
        assert e.value.data == {
            '@event': 'BROKEN_ARGS_DETECTED',
            '@type': 'error',
            'errors': {
                'id': [
                    'should not contain white characters.',
                ]
            }
        }


class DomainSerializerTestCase(TestCase):

    def test_serialization(self):

        d = Domain(
            id='super',
            name='Super Management')

        assert DomainSerializer(d).data == {
            '@type': 'domain',
            'id': 'super',
            'name': 'Super Management',
        }


@pytest.mark.parametrize(
    'description, expected',
    [
        # -- empty to empty
        (
            '',
            '',
        ),

        # -- nothing to transform
        (
            'hello world',
            'hello world',
        ),

        # -- prefix white chars
        (
            '\t\t   hello\n world',
            'hello world',
        ),

        # -- suffix white chars
        (
            'hello\n world \t\t\n  \n',
            'hello world',
        ),

        # -- single space delimiter
        (
            'hello\nworld',
            'hello world',
        ),
    ])
def test_transform_description(description, expected):

    m = Meta(title='...', domain=Domain(id='d', name='d'))

    assert m.transform_description(description) == expected

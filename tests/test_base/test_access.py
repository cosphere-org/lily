
from django.test import TestCase

from lily.base.access import Access, AccessSerializer


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


class AccessSerializerTestCase(TestCase):

    def test_serialize(self):

        a = Access(
            access_list=['SUPER_USER'],
            is_private=True)

        assert AccessSerializer(a).data == {
            '@type': 'access',
            'is_private': True,
            'access_list': ['SUPER_USER'],
        }

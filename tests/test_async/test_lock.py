# -*- coding: utf-8 -*-

from django.test import TestCase
import pytest
from mock import Mock, call

from async.lock import Lock


class LockTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixtures(self, mocker):
        self.mocker = mocker

    def test_acquire__success(self):

        lock_db = Mock(get=Mock(return_value=None))
        self.mocker.patch.object(Lock, 'db', lock_db)
        lock = Lock('some-lock-id')

        assert lock.acquire(1234) is True
        assert lock_db.get.call_args_list == [call('some-lock-id')]
        assert lock_db.set.call_args_list == [
            call('some-lock-id', True, 1234)]

    def test_acquire__already_locked(self):

        lock_db = Mock(get=Mock(return_value='lock'))
        self.mocker.patch.object(Lock, 'db', lock_db)
        lock = Lock('some-lock-id')

        assert lock.acquire(1234) is False
        assert lock_db.get.call_args_list == [call('some-lock-id')]

    def test_release(self):

        lock_db = Mock()
        self.mocker.patch.object(Lock, 'db', lock_db)
        lock = Lock('some-lock-id')

        lock.release()

        assert lock_db.delete.call_args_list == [call('some-lock-id')]

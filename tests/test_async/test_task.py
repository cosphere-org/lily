
from unittest import TestCase

from lily.async import AsyncTask


class AsyncTaskTestCase(TestCase):

    def test_init(self):

        def fn():
            pass

        task = AsyncTask(callback=fn, args=[9, 1])

        assert task.callback == fn
        assert task.args == [9, 1]
        assert task.successful is False
        assert task.result is None

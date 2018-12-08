
from unittest import TestCase
from time import time, sleep

from lily.async import AsyncTask, ParallelExecutor


class ParallelExecutorTestCase(TestCase):

    def test_execute__single_task(self):

        def success(x):
            sleep(0.5)
            return x ** 2

        t = AsyncTask(success, [4])

        ParallelExecutor(tasks=[t]).execute()

        assert t.result == 16
        assert t.successful is True

    def test_execute__many_tasks__all_successful(self):

        def success(x):
            sleep(0.5)
            return x ** 2

        t_0 = AsyncTask(success, [4])
        t_1 = AsyncTask(success, [6])
        t_2 = AsyncTask(success, [8])
        t_3 = AsyncTask(success, [9])

        start = time()
        ParallelExecutor(tasks=[t_0, t_1, t_2, t_3]).execute()
        end = time() - start

        assert end < 1
        assert t_0.result == 16
        assert t_0.successful is True
        assert t_1.result == 36
        assert t_1.successful is True
        assert t_2.result == 64
        assert t_2.successful is True
        assert t_3.result == 81
        assert t_3.successful is True

    def test_execute__many_tasks__one_failed(self):

        def success(x):
            sleep(0.5)
            return x ** 2

        def fail(x):
            raise Exception(x)

        t_0 = AsyncTask(success, [4])
        t_1 = AsyncTask(success, [6])
        t_2 = AsyncTask(fail, [8])

        start = time()
        ParallelExecutor(tasks=[t_0, t_1, t_2]).execute()
        end = time() - start

        assert end < 1
        assert t_0.result == 16
        assert t_0.successful is True
        assert t_1.result == 36
        assert t_1.successful is True
        assert isinstance(t_2.result, Exception)
        assert t_2.successful is False

    def test_execute__many_tasks__all_failed(self):

        def fail(x):
            raise Exception(x)

        t_0 = AsyncTask(fail, [4])
        t_1 = AsyncTask(fail, [6])
        t_2 = AsyncTask(fail, [8])

        start = time()
        ParallelExecutor(tasks=[t_0, t_1, t_2]).execute()
        end = time() - start

        assert end < 1
        assert isinstance(t_0.result, Exception)
        assert t_0.successful is False
        assert isinstance(t_1.result, Exception)
        assert t_1.successful is False
        assert isinstance(t_2.result, Exception)
        assert t_2.successful is False

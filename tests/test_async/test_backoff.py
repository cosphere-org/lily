
from unittest.mock import call
import asyncio

from django.test import TestCase
import pytest
import requests
from requests.exceptions import ConnectionError, Timeout

from lily.async import AsyncTask, BackoffExecutor


class Client:

    def task(self, task_id):

        return requests.get('http://hello.world/tasks/{}'.format(task_id))


class Response:

    def __init__(self, status_code, body={}):
        self.status_code = status_code
        self.body = body

    def __eq__(self, other):
        return (
            self.status_code == other.status_code and
            self.body == other.body)


async def async_sleep(*args):
    pass


class BackoffExecutorTestCase(TestCase):

    @pytest.fixture(autouse=True)
    def initfixture(self, mocker):
        self.mocker = mocker

    def test_single_request__all_successful(self):

        get = self.mocker.patch.object(requests, 'get')
        get.side_effect = [
            Response(200),
        ]

        responses = BackoffExecutor([
            AsyncTask(callback=Client().task, args=[11])
        ]).run()

        assert responses == [Response(200)]
        assert get.call_args_list == [call('http://hello.world/tasks/11')]

    def test_multiple_requests__all_successful(self):

        get = self.mocker.patch.object(requests, 'get')
        get.side_effect = [
            Response(200),
            Response(201),
            Response(403),
        ]

        responses = BackoffExecutor([
            AsyncTask(callback=Client().task, args=[11]),
            AsyncTask(callback=Client().task, args=[14]),
            AsyncTask(callback=Client().task, args=[16]),
        ]).run()

        assert responses == [
            Response(200),
            Response(201),
            Response(403),
        ]
        assert get.call_args_list == [
            call('http://hello.world/tasks/11'),
            call('http://hello.world/tasks/14'),
            call('http://hello.world/tasks/16'),
        ]

    def test_multiple_requests__some_successful__backoff(self):

        sleep = self.mocker.patch.object(asyncio, 'sleep')
        sleep.side_effect = async_sleep

        get = self.mocker.patch.object(requests, 'get')
        get.side_effect = [
            # 1st. round
            Response(200),    # 1.
            Exception,        # 2.
            ConnectionError,  # 3.

            # 2nd. round
            Timeout,          # 2.
            Response(201),    # 3.

            # 3rd. round
            Response(403),    # 2.
        ]

        responses = BackoffExecutor([
            AsyncTask(callback=Client().task, args=[11]),
            AsyncTask(callback=Client().task, args=[14]),
            AsyncTask(callback=Client().task, args=[16]),
        ]).run()

        assert responses == [
            Response(200),
            Response(403),
            Response(201),
        ]
        assert sleep.call_args_list == [call(0), call(2), call(8)]
        assert get.call_args_list == [
            # 1st. round
            call('http://hello.world/tasks/11'),
            call('http://hello.world/tasks/14'),
            call('http://hello.world/tasks/16'),

            # 2nd. round
            call('http://hello.world/tasks/14'),
            call('http://hello.world/tasks/16'),

            # 3rd. round
            call('http://hello.world/tasks/14'),
        ]

    def test_multiple_requests__till_backoff_exhaustion(self):

        sleep = self.mocker.patch.object(asyncio, 'sleep')
        sleep.side_effect = async_sleep

        get = self.mocker.patch.object(requests, 'get')
        get.side_effect = [
            # 1st. round
            Response(200),    # 1.
            Exception,        # 2.
            ConnectionError,  # 3.

            # 2nd. round
            Timeout,          # 2.
            Response(201),    # 3.

            # 3rd. round
            Response(403),    # 2.
        ]

        responses = BackoffExecutor(
            [
                AsyncTask(callback=Client().task, args=[11]),
                AsyncTask(callback=Client().task, args=[14]),
                AsyncTask(callback=Client().task, args=[16]),
            ],
            max_attempts=2).run()

        assert len(responses) == 3
        assert responses[0] == Response(200)
        assert isinstance(responses[1], Timeout) is True

        assert sleep.call_args_list == [call(0), call(2)]
        assert get.call_args_list == [
            # 1st. round
            call('http://hello.world/tasks/11'),
            call('http://hello.world/tasks/14'),
            call('http://hello.world/tasks/16'),

            # 2nd. round
            call('http://hello.world/tasks/14'),
            call('http://hello.world/tasks/16'),
        ]

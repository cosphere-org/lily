# -*- coding: utf-8 -*-

import asyncio


class AsyncTask:

    def __init__(self, callback, args):
        self.callback = callback
        self.args = args
        self.successful = False
        self.response = None


class BackoffExecutor:

    BACKOFF_UNIT = 3  # seconds

    BACKOFF_MAX_ATTEMPTS = 6

    def __init__(
            self,
            tasks,
            max_attempts=BACKOFF_MAX_ATTEMPTS,
            unit=BACKOFF_UNIT):

        self.tasks = tasks
        self.tasks_by_future = {}
        self.attempt_num = 0

        self.max_attempts = max_attempts
        self.unit = unit

        self.loop = asyncio.get_event_loop()

    async def step(self, attempt_num):

        futures = []
        idx = 0
        for task in self.tasks:
            if task.successful is False:
                futures.append(
                    self.loop.run_in_executor(
                        None,
                        task.callback,
                        *task.args
                    )
                )
                self.tasks_by_future[idx] = task
                idx += 1

        if futures:
            # -- sleep
            await asyncio.sleep(self.unit ** attempt_num - 1)

            requests = asyncio.gather(*futures, return_exceptions=True)
            for i, response in enumerate(await requests):
                task = self.tasks_by_future[i]
                if not isinstance(response, Exception):
                    task.successful = True

                task.response = response

        return (
            all([task.successful for task in self.tasks]),
            [task.response for task in self.tasks])

    def run(self):

        for i in range(self.max_attempts):

            done, responses = self.loop.run_until_complete(self.step(i))
            if done:
                return responses

        return responses

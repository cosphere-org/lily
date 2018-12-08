
import asyncio


from .task import AsyncTask


class BackoffExecutor:

    BACKOFF_UNIT = 3  # seconds

    BACKOFF_MAX_ATTEMPTS = 6

    def __init__(
            self,
            tasks: [AsyncTask],
            max_attempts=BACKOFF_MAX_ATTEMPTS,
            unit=BACKOFF_UNIT):

        self.tasks = tasks
        self.tasks_by_future = {}
        self.attempt_num = 0

        self.max_attempts = max_attempts
        self.unit = unit

    async def step(self, loop, attempt_num):

        futures = []
        idx = 0
        for task in self.tasks:
            if task.successful is False:
                futures.append(
                    loop.run_in_executor(
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

            future_results = asyncio.gather(*futures, return_exceptions=True)
            for i, result in enumerate(await future_results):
                task = self.tasks_by_future[i]
                if not isinstance(result, Exception):
                    task.successful = True

                task.result = result

        return (
            all([task.successful for task in self.tasks]),
            [task.result for task in self.tasks])

    def run(self):

        loop = asyncio.new_event_loop()

        for i in range(self.max_attempts):

            done, responses = loop.run_until_complete(self.step(loop, i))
            if done:
                loop.close()
                return responses

        loop.close()
        return responses

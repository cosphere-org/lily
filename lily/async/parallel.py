
import asyncio
import concurrent.futures

from .task import AsyncTask


class ParallelExecutor:

    BACKOFF_UNIT = 3  # seconds

    def __init__(self, tasks: [AsyncTask]):

        self.tasks = tasks

    async def async_execute(self, loop):

        with concurrent.futures.ThreadPoolExecutor() as pool:
            futures = [
                loop.run_in_executor(pool, task.callback, *task.args)
                for task in self.tasks]

        responses = asyncio.gather(*futures, return_exceptions=True)
        for i, response in enumerate(await responses):
            self.tasks[i].response = response
            self.tasks[i].successful = not isinstance(response, Exception)

        return self.tasks

    def execute(self):

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.async_execute(loop))
        loop.close()

        return result

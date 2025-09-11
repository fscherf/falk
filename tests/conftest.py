import concurrent
import threading
import asyncio

import pytest


def pytest_collection_modifyitems(session, config, items):
    # The test suite is organized in stages that build upon each other.
    # This hook ensures that the tests modules ordered by name so they get
    # executed in the right order.

    items.sort(key=lambda item: item.fspath.strpath)


class BackgroundLoop:
    def __init__(self):
        self.loop = None

        self._started = concurrent.futures.Future()
        self._stopped = None
        self._thread = None

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()

        asyncio.set_event_loop(self.loop)

        try:
            main_task = self.loop.create_task(
                coro=self._keep_loop_open(),
            )

            self.loop.run_until_complete(main_task)

        finally:
            self.loop.stop()
            self.loop.close()

    async def _keep_loop_open(self):

        # start
        self._stopped = asyncio.Future()
        self._started.set_result(None)

        # main "loop"
        await self._stopped

        # stop
        # cancel tasks
        canceled_tasks = []
        current_task = asyncio.current_task(loop=self.loop)

        for task in asyncio.all_tasks():
            if task.done() or task is current_task:
                continue

            task.cancel()
            canceled_tasks.append(task)

        for task in canceled_tasks:
            try:
                await task

            except asyncio.CancelledError:
                pass

    def start(self):
        self._thread = threading.Thread(
            target=self._run_loop,
        )

        self._thread.start()

        self._started.result()

    def stop(self):
        async def _stop():
            self._stopped.set_result(None)

        concurrent_future = asyncio.run_coroutine_threadsafe(
            coro=_stop(),
            loop=self.loop,
        )

        return concurrent_future.result()


@pytest.fixture
def loop():
    background_loop = BackgroundLoop()

    background_loop.start()

    yield background_loop.loop

    background_loop.stop()

from threading import Thread
import concurrent
import asyncio

from aiohttp.web import AppRunner, TCPSite
import pytest

from falk.contrib.aiohttp import get_aiohttp_app
from falk.apps import run_configure_app


class AiohttpAppRunner:
    def __init__(self):
        self._app = None
        self._site = None
        self._loop = None
        self._started = None
        self._stopped = None
        self._thread = None
        self._host = None
        self._port = None

    async def _run_app(self):
        runner = AppRunner(self._app)

        await runner.setup()

        self._site = TCPSite(
            runner=runner,
            host=self._host,
            port=self._port,
        )

        await self._site.start()

        self._started.set_result(None)

        await self._stopped

        await runner.cleanup()

    async def _set_stopped(self):
        self._stopped.set_result(None)

    def _run_loop_in_thread(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stopped = asyncio.Future(loop=self._loop)

        self._loop.run_until_complete(self._run_app())

    def start(self, app, host="127.0.0.1", port=0):
        self._app = app
        self._host = host
        self._port = port
        self._started = concurrent.futures.Future()

        self._thread = Thread(
            target=self._run_loop_in_thread,
        )

        self._thread.start()
        self._started.result()

    def stop(self):
        future = asyncio.run_coroutine_threadsafe(
            coro=self._set_stopped(),
            loop=self._loop,
        )

        future.result()

    def get_base_url(self):
        host, port = self._site._server.sockets[0].getsockname()

        return f"http://{host}:{port}"


@pytest.fixture
def start_falk_app():
    aiohttp_app_runner = AiohttpAppRunner()

    def _start_falk_app(configure_app, host="127.0.0.1", port=0, threads=4):
        mutable_app = run_configure_app(configure_app)

        aiohttp_app = get_aiohttp_app(
            mutable_app=mutable_app,
            threads=threads,
        )

        aiohttp_app_runner.start(
            app=aiohttp_app,
            host=host,
            port=port,
        )

        return mutable_app, aiohttp_app_runner.get_base_url()

    yield _start_falk_app

    aiohttp_app_runner.stop()

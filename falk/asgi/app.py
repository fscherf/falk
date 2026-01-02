from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging

from falk.asgi.request_handling import handle_http_request
from falk.asgi.websockets import handle_websocket
from falk.asgi.lifespans import handle_lifespan
from falk.apps import run_configure_app

logger = logging.getLogger("falk")


def get_asgi_app(configure_app=None, mutable_app=None):
    mutable_app = mutable_app or {}

    async def app(scope, receive, send):
        # FIXME: if `mutable_app` is provided, the executor is never set up

        # setup
        if not mutable_app:
            try:
                mutable_app.update(
                    run_configure_app(configure_app),
                )

            except Exception:
                logger.exception("exception raised while setting up the app")

                raise

            # setup async support
            loop = asyncio.get_running_loop()

            def run_coroutine_sync(coroutine):
                future = asyncio.run_coroutine_threadsafe(
                    coro=coroutine,
                    loop=loop,
                )

                return future.result()

            mutable_app["settings"]["run_coroutine_sync"] = run_coroutine_sync

            # setup sync support
            mutable_app["executor"] = ThreadPoolExecutor(
                max_workers=mutable_app["settings"]["workers"],
            )

        # lifespans
        if scope["type"] == "lifespan":
            await handle_lifespan(
                mutable_app=mutable_app,
                scope=scope,
                receive=receive,
                send=send,
            )

            return

        # websockets
        elif scope["type"] == "websocket":
            await handle_websocket(
                mutable_app=mutable_app,
                scope=scope,
                receive=receive,
                send=send,
            )

            return

        event = await receive()

        # http.request
        if event["type"] == "http.request":
            await handle_http_request(
                mutable_app,
                event=event,
                scope=scope,
                receive=receive,
                send=send,
            )

    return app

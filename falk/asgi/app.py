from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging

from falk.asgi.request_handling import handle_http_request
from falk.asgi.websockets import handle_websocket
from falk.asgi.lifespans import handle_lifespan
from falk.apps import run_configure_app
from falk.routing import get_component

logger = logging.getLogger("falk")


def get_asgi_app(configure_app=None, mutable_app=None):
    mutable_app = mutable_app or {}

    async def app(scope, receive, send):
        # FIXME: if `mutable_app` is provided, the executor is never set up

        loop = asyncio.get_running_loop()

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

            # run checks
            if mutable_app["settings"]["debug"]:
                logger.warning("falk is running in debug mode")

        # lifespans
        if scope["type"] == "lifespan":
            await handle_lifespan(
                mutable_app=mutable_app,
                scope=scope,
                receive=receive,
                send=send,
            )

            return

        # mounted ASGI apps
        asgi_component, _ = await loop.run_in_executor(
            mutable_app["executor"],
            lambda: get_component(
                routes=mutable_app["routes"],
                path=scope["path"],
                asgi_interface=True,
            )
        )

        if asgi_component:
            try:
                return await asgi_component(
                    mutable_app=mutable_app,
                    asgi_scope=scope,
                    asgi_receive=receive,
                    asgi_send=send,
                )

            except Exception:
                logger.exception(
                    "exception raised while running %s",
                    asgi_component,
                )

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

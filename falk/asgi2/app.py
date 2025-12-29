from contextlib import asynccontextmanager

from starlette.concurrency import run_in_threadpool
from starlette.routing import WebSocketRoute, Route
from starlette.applications import Starlette

from falk.asgi2.request_handling import handle_starlette_request
from falk.asgi2.websockets import handle_websocket
from falk.apps import run_configure_app


def get_asgi2_app(configure_app=None, mutable_app=None):
    if not mutable_app:
        mutable_app = run_configure_app(configure_app)

    @asynccontextmanager
    async def lifespan(starlette_app):
        await run_in_threadpool(
            lambda: mutable_app["entry_points"]["on_startup"](
                mutable_app=mutable_app,
            ),
        )

        yield

        await run_in_threadpool(
            lambda: mutable_app["entry_points"]["on_shutdown"](
                mutable_app=mutable_app,
            ),
        )

    async def _handle_request(request):
        return await handle_starlette_request(
            mutable_app=mutable_app,
            starlette_request=request,
        )

    async def _handle_websocket(websocket):
        if not mutable_app["settings"]["websockets"]:
            await websocket.close()

            return

        await handle_websocket(
            mutable_app=mutable_app,
            websocket=websocket,
        )

    asgi_app = Starlette(
        routes=[
            Route("/{path:path}", _handle_request, methods=["GET", "POST"]),
            WebSocketRoute("/{path:path}", _handle_websocket),
        ],
        lifespan=lifespan,
    )

    return asgi_app

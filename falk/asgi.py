from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs
import mimetypes
import asyncio
import logging
import json
import os

from falk.request_handling import get_request
from falk.http import get_header, set_header
from falk.apps import run_configure_app
import aiofiles

CHUNK_SIZE = 64 * 1024  # 64 KiB

logger = logging.getLogger("falk")


async def run_entry_point(mutable_app, entry_point):
    loop = asyncio.get_event_loop()

    def _func():
        try:
            entry_point(mutable_app)

        except Exception:
            logger.exception(
                "exception raised while running %s",
                entry_point,
            )

    return loop.run_in_executor(
        executor=mutable_app["executor"],
        func=_func,
    )


async def shutdown(mutable_app, send):
    await run_entry_point(
        mutable_app=mutable_app,
        entry_point=mutable_app["entry_points"]["on_shutdown"],
    )

    if mutable_app["executor"]:
        mutable_app["executor"].shutdown(
            wait=False,
        )

    await send({"type": "lifespan.shutdown.complete"})


async def handle_lifespan(mutable_app, scope, receive, send):
    try:
        while True:
            event = await receive()

            # startup
            if event["type"] == "lifespan.startup":
                await run_entry_point(
                    mutable_app=mutable_app,
                    entry_point=mutable_app["entry_points"]["on_startup"],
                )

                await send({"type": "lifespan.startup.complete"})

            # shutdown
            elif event["type"] == "lifespan.shutdown":
                await shutdown(
                    mutable_app=mutable_app,
                    send=send,
                )

                break

    # unplanned shutdown
    except asyncio.CancelledError:
        await shutdown(
            mutable_app=mutable_app,
            send=send,
        )

    except Exception:
        logger.exception("exception raised while handling lifespan events")

        if event["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.failed"})

        else:
            await send({"type": "lifespan.shutdown.failed"})

        raise


def _handle_falk_request(mutable_app, scope, body):

    # setup request
    query = parse_qs(scope["query_string"].decode())
    headers = {}

    for name, value in scope.get("headers", []):
        set_header(
            headers=headers,
            name=name.decode("utf-8"),
            value=value.decode("utf-8"),
        )

    content_type = get_header(
        headers=headers,
        name="Content-Type",
        default="",
    )

    content_length = get_header(
        headers=headers,
        name="Content-Length",
        default="0",
    )

    request_kwargs = {
        "protocol": "HTTP",
        "headers": headers,
        "method": scope["method"],
        "path": scope["path"],
        "content_type": content_type,
        "query": query,
    }

    if scope["method"] == "POST":
        if content_length.isnumeric():
            content_length = int(content_length)
            body = body[0:content_length].decode("utf-8")

            if content_type == "application/json":
                request_kwargs["json"] = json.loads(body)

            elif content_type == "application/x-www-form-urlencoded":
                request_kwargs["post"] = parse_qs(body)

    request = get_request(**request_kwargs)

    # handle request
    response = mutable_app["entry_points"]["handle_request"](
        request=request,
        mutable_app=mutable_app,
    )

    # encode response
    if response["json"]:
        response["body"] = json.dumps(response["json"])

    set_header(
        headers=response["headers"],
        name="content-length",
        value=str(len(response["body"].encode("utf-8"))),
    )

    response["headers"] = [
        (k.encode(), v.encode()) for k, v in response["headers"].items()
    ]

    response["body"] = response["body"].encode()

    return response


def _handle_websocket_message(mutable_app, scope, text):

    # setup request
    request_id, json_data = json.loads(text)
    query = parse_qs(scope["query_string"].decode())
    headers = {}

    for name, value in scope.get("headers", []):
        headers[name.decode("utf-8")] = value.decode("utf-8")

    request = get_request(
        protocol="WS",
        headers=headers,
        method="POST",
        path=scope["path"],
        content_type="application/json",
        query=query,
        json=json_data,
    )

    # handle request
    response = mutable_app["entry_points"]["handle_request"](
        request=request,
        mutable_app=mutable_app,
    )

    return json.dumps([request_id, response])


async def handle_websocket(mutable_app, scope, receive, send):
    loop = asyncio.get_event_loop()

    while True:
        event = await receive()

        # websocket.connect
        if event["type"] == "websocket.connect":
            if mutable_app["settings"]["websockets"]:
                await send({"type": "websocket.accept"})

            else:
                await send({"type": "websocket.close"})

        # websocket.disconnect
        elif event["type"] == "websocket.disconnect":
            break

        # websocket.receive
        elif event["type"] == "websocket.receive":
            response_string = await loop.run_in_executor(
                mutable_app["executor"],
                lambda: _handle_websocket_message(
                    mutable_app=mutable_app,
                    scope=scope,
                    text=event["text"],
                ),
            )

            await send({
                "type": "websocket.send",
                "text": response_string,
            })


async def handle_http_file_response(response, send):
    abs_path = response["file_path"]
    rel_path = os.path.basename(abs_path)
    file_size = os.path.getsize(abs_path)
    mime = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"

    headers = [
        (b"content-type", mime.encode()),

        (b"content-disposition",
         f'attachment; filename="{rel_path}"'.encode()),

        (b"content-length", str(file_size).encode()),
    ]

    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": headers,
    })

    bytes_sent = 0

    async with aiofiles.open(abs_path, "rb") as f:
        while True:
            chunk = await f.read(CHUNK_SIZE)

            if not chunk:
                break

            bytes_sent += len(chunk)
            more = bytes_sent < file_size

            await send({
                "type": "http.response.body",
                "body": chunk,
                "more_body": more,
            })


async def handle_http_request(mutable_app, event, scope, receive, send):
    loop = asyncio.get_event_loop()

    # read body
    body = event.get("body", b"")

    while event.get("more_body", False):
        event = await receive()

        body += event.get("body", b"")

    # handle request
    response = await loop.run_in_executor(
        mutable_app["executor"],
        lambda: _handle_falk_request(mutable_app, scope, body),
    )

    if response["file_path"]:
        await handle_http_file_response(
            response=response,
            send=send,
        )

    else:
        await send({
            "type": "http.response.start",
            "status": response["status"],
            "headers": response["headers"],
        })

        await send({
            "type": "http.response.body",
            "body": response["body"],
        })


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

from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging
import json

from aiohttp.web import (
    WebSocketResponse,
    json_response,
    FileResponse,
    Application,
    WSMsgType,
    Response,
    route,
)

from falk.contrib.asyncio import configure_run_coroutine_sync
from falk.request_handling import get_request

logger = logging.getLogger("falk")


async def aiohttp_request_to_falk_request(aiohttp_request):
    # TODO: add host, user agent, query

    request_args = {
        "method": aiohttp_request.method,
        "path": aiohttp_request.url.path,
        "headers": dict(aiohttp_request.headers),
        "content_type": aiohttp_request.content_type,
        "post": {},
        "json": {},
    }

    if aiohttp_request.method == "POST":
        request_args["post"] = await aiohttp_request.post()

        if aiohttp_request.content_type == "application/json":
            request_args["json"] = await aiohttp_request.json()

    return get_request(**request_args)


def aiohttp_websocket_message_to_falk_request(
        aiohttp_request,
        message_data,
):

    request_args = {
        "protocol": "WS",
        "method": "POST",
        "path": aiohttp_request.url.path,
        "headers": dict(aiohttp_request.headers),
        "content_type": "application/json",
        "post": {},
        "json": message_data,
    }

    return get_request(**request_args)


async def falk_response_to_aiohttp_response(falk_response):

    # JSON response
    if falk_response["json"]:
        return json_response(
            status=falk_response["status"],
            headers=falk_response["headers"],
            data=falk_response["json"],
        )

    # file response
    if falk_response["file_path"]:
        return FileResponse(
            status=falk_response["status"],
            headers=falk_response["headers"],
            path=falk_response["file_path"],
        )

    # text response
    return Response(
        status=falk_response["status"],
        headers=falk_response["headers"],
        charset=falk_response["charset"],
        content_type=falk_response["content_type"],
        body=falk_response["body"],
    )


def get_aiohttp_app(mutable_app, threads=4):
    aiohttp_app = Application()

    executor = ThreadPoolExecutor(
        max_workers=threads,
        thread_name_prefix="falk.worker",
    )

    settings = mutable_app["settings"]
    falk_request_handler = mutable_app["entry_points"]["handle_request"]

    def handle_aiohttp_websocket_message(aiohttp_request, message_string):
        message_id, message_data = json.loads(message_string)

        falk_request = aiohttp_websocket_message_to_falk_request(
            aiohttp_request=aiohttp_request,
            message_data=message_data,
        )

        falk_response = falk_request_handler(
            request=falk_request,
            mutable_app=mutable_app,
        )

        return json.dumps([
            message_id,
            falk_response,
        ])

    async def handle_aiohttp_websocket_request(aiohttp_request):
        loop = aiohttp_request.app["loop"]
        aiohttp_websocket_response = WebSocketResponse()

        await aiohttp_websocket_response.prepare(aiohttp_request)

        try:
            async for message in aiohttp_websocket_response:
                if message.type == WSMsgType.TEXT:
                    response_message = await loop.run_in_executor(
                        executor,
                        lambda: handle_aiohttp_websocket_message(
                            aiohttp_request=aiohttp_request,
                            message_string=message.data,
                        ),
                    )

                    await aiohttp_websocket_response.send_str(response_message)

                elif message.type == WSMsgType.PING:
                    await aiohttp_websocket_response.pong()

                elif message.type in (WSMsgType.CLOSED, WSMsgType.ERROR):
                    break

        except asyncio.CancelledError:
            pass

        finally:
            await aiohttp_websocket_response.close()

        return aiohttp_websocket_response

    async def handle_aiohttp_request(aiohttp_request):
        loop = aiohttp_request.app["loop"]

        # websocket request
        upgrade_header = aiohttp_request.headers.get("Upgrade", "").lower()

        if aiohttp_request.method == "GET" and upgrade_header == "websocket":
            if not settings["websockets"]:
                return Response(
                    status=426,
                    content_type="application/json",
                    text='{"error": "websocket requests are disabled"}',
                )

            return await handle_aiohttp_websocket_request(aiohttp_request)

        # HTTP request
        falk_request = await aiohttp_request_to_falk_request(
            aiohttp_request=aiohttp_request,
        )

        def _handle_aiohttp_request():
            falk_request_handler = (
                mutable_app["entry_points"]["handle_request"])

            return falk_request_handler(
                request=falk_request,
                mutable_app=mutable_app,
            )

        falk_response = await loop.run_in_executor(
            executor,
            _handle_aiohttp_request,
        )

        aiohttp_response = await falk_response_to_aiohttp_response(
            falk_response=falk_response,
        )

        return aiohttp_response

    async def on_startup(aiohttp_app):
        configure_run_coroutine_sync(
            mutable_app=mutable_app,
        )

        aiohttp_app["loop"] = asyncio.get_event_loop()

    async def on_cleanup(aiohttp_app):
        logger.info("shutting down")

    aiohttp_app.on_startup.append(on_startup)
    aiohttp_app.on_cleanup.append(on_cleanup)

    aiohttp_app.add_routes([
        route("*", "/{path:.*}", handle_aiohttp_request),
    ])

    return aiohttp_app

from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging

from aiohttp.web import Application, Response, route

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


async def falk_response_to_aiohttp_response(falk_response):
    # TODO: add support for file and JSON responses

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

    async def handle_aiohttp_request(aiohttp_request):
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

        falk_response = await aiohttp_request.app["loop"].run_in_executor(
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

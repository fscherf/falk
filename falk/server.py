from concurrent.futures import ThreadPoolExecutor
from argparse import ArgumentParser
import asyncio
import logging
import socket
import sys

from falk.request_handling import get_request
from falk.imports import import_by_string
from falk.app import get_default_app


def get_app(default_app):
    return default_app


if __name__ == "__main__":
    argument_parser = ArgumentParser(
        prog="falk",
    )

    argument_parser.add_argument(
        "--app",
        default="falk.server.get_app",
    )

    argument_parser.add_argument(
        "-l",
        "--log-level",
        choices=["debug", "info", "warn", "error", "critical"],
        default="info",
        help="log level (default: %(default)r)",
    )

    argument_parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="127.0.0.1",
        help="TCP/IP host to serve on (default: %(default)r)",
    )

    argument_parser.add_argument(
        "-P",
        "--port",
        type=int,
        default=8000,
        help="TCP/IP port to serve on (default: %(default)r)",
    )

    argument_parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=4,
        help="number of worker threads (default: %(default)r)",
    )

    # parse command line arguments
    args = argument_parser.parse_args()

    # import dependencies
    # these are additional dependencies, so this might fail
    try:
        from aiohttp.web import Application, Response, route, run_app
        import simple_logging_setup

    except ImportError as exception:
        argument_parser.error(f"missing dependencies: {exception}")

    # setup logging
    simple_logging_setup.setup(
        level=args.log_level,
        preset="service",
    )

    logger = logging.getLogger("falk")

    # setup app
    try:
        get_falk_app = import_by_string(args.app)

    except ImportError as exception:
        argument_parser.error(str(exception))

    falk_app = get_falk_app(get_default_app())

    # setup thread pool
    executor = ThreadPoolExecutor(
        max_workers=args.threads,
        thread_name_prefix="falk.worker",
    )

    # setup aiohttp server
    async def handle_aiohttp_request(aiohttp_request):
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

        falk_request = get_request(**request_args)

        def _handle_aiohttp_request():
            falk_request_handler = falk_app["entry_points"]["handle_request"]

            falk_response = falk_request_handler(
                request=falk_request,
                app=falk_app,
            )

            return Response(
                status=falk_response["status"],
                headers=falk_response["headers"],
                charset=falk_response["charset"],
                content_type=falk_response["content_type"],
                body=falk_response["body"],
            )

        return await aiohttp_request.app["loop"].run_in_executor(
            executor,
            _handle_aiohttp_request,
        )

    async def on_startup(aiohttp_app):
        aiohttp_app["loop"] = asyncio.get_event_loop()

    async def on_cleanup(aiohttp_app):
        logger.info("shutting down")

    aiohttp_app = Application()

    aiohttp_app.on_startup.append(on_startup)
    aiohttp_app.on_cleanup.append(on_cleanup)

    aiohttp_app.add_routes([
        route("*", "/{path:.*}", handle_aiohttp_request),
    ])

    # start aiohttp server
    try:
        run_app(
            app=aiohttp_app,
            host=args.host,
            port=args.port,
            access_log=None,
        )

        executor.shutdown()

    except (OSError, socket.gaierror):
        logger.exception("exception raised while running aiohttp server")

        sys.exit(1)

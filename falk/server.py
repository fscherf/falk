from argparse import ArgumentParser
import logging
import socket
import sys

from falk.imports import import_by_string
from falk.apps import run_configure_app


def configure_app():
    pass


if __name__ == "__main__":
    argument_parser = ArgumentParser(
        prog="falk",
    )

    argument_parser.add_argument(
        "-c",
        "--configure-app",
        default="falk.server.configure_app",
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
        from aiohttp.web import run_app
        import simple_logging_setup

        from falk.contrib.aiohttp import get_aiohttp_app

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
        _configure_app = import_by_string(args.configure_app)

    except ImportError as exception:
        argument_parser.error(str(exception))

    falk_app = run_configure_app(_configure_app)
    aiohttp_app = get_aiohttp_app(falk_app, threads=args.threads)

    # start aiohttp server
    try:
        run_app(
            app=aiohttp_app,
            host=args.host,
            port=args.port,
            access_log=None,
        )

    except (OSError, socket.gaierror):
        logger.exception("exception raised while running aiohttp server")

        sys.exit(1)

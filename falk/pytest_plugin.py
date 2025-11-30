from threading import Thread
import contextlib
import time

from uvicorn.middleware.wsgi import WSGIMiddleware
import uvicorn
import pytest

from falk.apps import run_configure_app
from falk.asgi import get_asgi_app
from falk.wsgi import get_wsgi_app


@pytest.fixture
def start_falk_app():
    state = {
        "uvicorn_server": None,
        "uvicorn_thread": None,
    }

    def _stop_falk_app():
        # check if app was already stopped by the test
        if not state["uvicorn_server"] or state["uvicorn_server"].should_exit:
            return

        state["uvicorn_server"].should_exit = True

        state["uvicorn_thread"].join()

    def _start_falk_app(
            configure_app,
            host="127.0.0.1",
            port=0,
            interface="asgi",
            startup_retry_delay_in_s=0.01,
            startup_timeout_in_s=5.0,
    ):

        if interface not in ("wsgi", "asgi"):
            raise ValueError(
                f'Unknwon interface "{interface}". Supported interfaces: asgi, wsgi',
            )

        # configure falk app
        mutable_app = run_configure_app(configure_app)

        if interface == "asgi":
            uvicorn_app = get_asgi_app(
                mutable_app=mutable_app,
            )

        else:
            uvicorn_app = WSGIMiddleware(
                get_wsgi_app(
                    mutable_app=mutable_app,
                ),
            )

        # start uvicorn server
        state["uvicorn_server"] = uvicorn.Server(
            config=uvicorn.Config(
                app=uvicorn_app,
                host=host,
                port=port,
                log_config=None,
            ),
        )

        state["uvicorn_thread"] = Thread(
            target=lambda: state["uvicorn_server"].run(),
        )

        state["uvicorn_thread"].start()

        # wait for uvicorn to open a port
        base_url = ""
        start = time.monotonic()

        while True:
            with contextlib.suppress(Exception):
                if state["uvicorn_server"].servers:
                    socket = state["uvicorn_server"].servers[0].sockets[0]
                    host, port = socket.getsockname()
                    base_url = f"http://{host}:{port}"

                    break

            if time.monotonic() - start > startup_timeout_in_s:
                raise TimeoutError(
                    f"app did not start within {startup_timeout_in_s} seconds",
                )

            time.sleep(startup_retry_delay_in_s)

        return mutable_app, base_url

    # run test
    yield _start_falk_app

    # cleanup
    _stop_falk_app()

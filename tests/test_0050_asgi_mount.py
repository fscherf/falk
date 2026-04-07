import pytest


def get_falk_app(events=None):
    from falk.asgi import get_asgi_app

    if events is None:
        events = []

    def Index(set_response_body):
        set_response_body("falk: /")

    def SubPage(set_response_body):
        set_response_body("falk: /foo")

    def SubSubPage(set_response_body):
        set_response_body("falk: /foo/bar")

    def startup(mutable_app):
        events.append("startup")

    def shutdown(mutable_app):
        events.append("shutdown")

    def configure_app(add_route, add_startup_callback, add_shutdown_callback):
        add_route("/foo/bar", SubSubPage)
        add_route("/foo/", SubPage)
        add_route("/", Index)

        add_startup_callback(startup)
        add_shutdown_callback(shutdown)

    return get_asgi_app(configure_app)


def get_starlette_app(events=None):
    from contextlib import asynccontextmanager

    from starlette.responses import PlainTextResponse
    from starlette.applications import Starlette
    from starlette.routing import Route

    if events is None:
        events = []

    async def index(request):
        return PlainTextResponse("starlette: /")

    async def sub_page(request):
        return PlainTextResponse("starlette: /foo")

    async def sub_sub_page(request):
        return PlainTextResponse("starlette: /foo/bar")

    @asynccontextmanager
    async def lifespan(app):
        events.append("startup")

        yield

        events.append("shutdown")

    app = Starlette(
        routes=[
            Route("/foo/bar", sub_sub_page),
            Route("/foo/", sub_page),
            Route("/", index),
        ],
        lifespan=lifespan,
    )

    return app


def get_asgi_app(app_name, *args, **kwargs):
    return {
        "falk": get_falk_app,
        "starlette": get_starlette_app,
    }[app_name](*args, **kwargs)


@pytest.mark.parametrize("app_name", ["falk", "starlette"])
def test_mount_asgi_app(app_name, start_falk_app):
    from falk.asgi import Mount

    import requests

    asgi_app = get_asgi_app(app_name)

    def Index(set_response_body):
        return set_response_body("index")

    def configure_app(add_route):
        add_route("/foo/<path:.*>", Mount(asgi_app))
        add_route("/", Index)

    _, base_url, _ = start_falk_app(configure_app)

    def get_text(path=""):
        return requests.get(base_url + path).text

    assert get_text("/foo/bar") == f"{app_name}: /foo/bar"
    assert get_text("/foo/") == f"{app_name}: /foo"
    assert get_text("/") == "index"


@pytest.mark.parametrize("app_name", ["falk", "starlette"])
def test_mount_asgi_app_behind_prefix(app_name, start_falk_app):
    from falk.asgi import Mount

    import requests

    asgi_app = get_asgi_app(app_name)

    def Index(set_response_body):
        return set_response_body("index")

    def configure_app(add_route):
        add_route("/asgi-app/<path:.*>", Mount(asgi_app, prefix="/asgi-app"))
        add_route("/", Index)

    _, base_url, _ = start_falk_app(configure_app)

    def get_text(path=""):
        return requests.get(base_url + path).text

    assert get_text("/asgi-app/foo/bar") == f"{app_name}: /foo/bar"
    assert get_text("/asgi-app/foo/") == f"{app_name}: /foo"
    assert get_text("/asgi-app/") == f"{app_name}: /"
    assert get_text("/") == "index"


@pytest.mark.xfail
@pytest.mark.parametrize("enabled", [True, False])
def test_lifespans(enabled, start_falk_app):
    # TODO: implement

    from falk.asgi import Mount

    falk_events = []
    starlette_events = []

    falk_app = get_falk_app(falk_events)
    starlette_app = get_starlette_app(starlette_events)

    def configure_app(add_route):
        add_route("/", Mount(falk_app, lifespan=enabled))
        add_route("/", Mount(starlette_app, lifespan=enabled))

    # startup hook
    _, _, stop_app = start_falk_app(configure_app)

    if enabled:
        assert falk_events == ["startup"]
        assert starlette_events == ["startup"]

    else:
        assert falk_events == []
        assert starlette_events == []

    # shutdown hook
    stop_app()

    if enabled:
        assert falk_events == ["startup", "shutdown"]
        assert starlette_events == ["startup", "shutdown"]

    else:
        assert falk_events == []
        assert starlette_events == []

def _get_aiohttp_test_app():
    from aiohttp.web import Application, Response, route

    app = Application()

    async def handle_request(request):
        return Response(
            content_type="text/html",
            text='<h1 id="hello-world">Hello World</h1>',
        )

    app.add_routes([
        route("*", "/{path:.*}", handle_request),
    ])

    return app


def test_package():
    import falk  # NOQA


def test_aiohttp_app_runner():
    import requests

    from falk.pytest_plugin import AiohttpAppRunner

    aiohttp_app_runner = AiohttpAppRunner()

    aiohttp_app_runner.start(_get_aiohttp_test_app())

    try:
        response = requests.get(aiohttp_app_runner.get_base_url())

        assert response.status_code == 200
        assert "Hello World" in response.text

    finally:
        aiohttp_app_runner.stop()


def test_playwright_browser(page):
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(
            temp_dir,
            "hello-world.html",
        )

        with open(path, "w+") as file_handle:
            file_handle.write(
                '<h1 id="hello-world">Hello World</h1>'
            )

        page.goto(f"file://{path}")

        assert page.inner_text("#hello-world") == "Hello World"

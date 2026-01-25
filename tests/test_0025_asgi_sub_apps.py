import pytest


def test_request_attributes(start_falk_app):
    from starlette.applications import Starlette
    from starlette.routing import Mount
    import requests

    from falk.asgi import get_asgi_app

    def Index(request, set_response_json, get_url):
        set_response_json({
            "raw_path": request["raw_path"],
            "root_path": request["root_path"],
            "path": request["path"],
            "sub_page": get_url("sub-page"),
        })

    def SubPage(set_response_json):
        set_response_json({})

    def configure_app(add_route):
        add_route("/sub-page(/)", SubPage, name="sub-page")
        add_route("/", Index)

    falk_app = get_asgi_app(configure_app)

    starlette_app = Starlette(
        routes=[
            Mount("/prefix1", app=falk_app),
            Mount("/prefix2/", app=falk_app),
            Mount("/", app=falk_app),
        ]
    )

    _, base_url = start_falk_app(
        asgi_app=starlette_app,
    )

    # no prefix
    response = requests.get(base_url + "/")

    assert response.json() == {
        "raw_path": "/",
        "root_path": "",
        "path": "/",
        "sub_page": "/sub-page/",
    }

    # prefix1
    response = requests.get(base_url + "/prefix1/")

    assert response.json() == {
        "raw_path": "/prefix1/",
        "root_path": "/prefix1",
        "path": "/",
        "sub_page": "/prefix1/sub-page/",
    }

    # prefix2
    response = requests.get(base_url + "/prefix2/")

    assert response.json() == {
        "raw_path": "/prefix2/",
        "root_path": "/prefix2",
        "path": "/",
        "sub_page": "/prefix2/sub-page/",
    }


@pytest.mark.only_browser("chromium")
def test_urls(start_falk_app, page):
    import os

    from playwright.sync_api import expect
    from starlette.applications import Starlette
    from starlette.routing import Mount
    import requests

    from test_app.app import configure_app
    import test_app

    from falk.static_files import get_falk_static_dir
    from falk.asgi import get_asgi_app

    falk_app = get_asgi_app(configure_app)

    starlette_app = Starlette(
        routes=[
            Mount("/prefix1", app=falk_app),
            Mount("/prefix2/", app=falk_app),
            Mount("/", app=falk_app),
        ]
    )

    _, base_url = start_falk_app(
        asgi_app=starlette_app,
    )

    # find test app base.css content
    base_css_path = os.path.join(
        os.path.dirname(test_app.__file__),
        "static/base.css",
    )

    base_css_content = open(base_css_path, "r").read()

    # find falk client content
    falk_client_path = get_falk_static_dir() + "/falk/falk.js"
    falk_client_content = open(falk_client_path, "r").read()

    # test prefixes
    prefixes = ["/", "/prefix1/", "/prefix2/"]

    for prefix in prefixes:

        # prefix in links
        page.goto(base_url + prefix)
        locator = page.locator("a#home")
        expect(locator).to_have_attribute("href", prefix)

        # CSS URLs
        page.wait_for_selector(
            f'link[href="{prefix}static/base.css"]',
            state="attached",
        )

        requests.get(
            f"{base_url}/{prefix}static/base.css",
        ).text == base_css_content

        # prefix in script URLs
        page.wait_for_selector(
            f'script[src="{prefix}static/falk/falk.js"]',
            state="attached",
        )

        requests.get(
            f"{base_url}/{prefix}static/falk/falk.js",
        ).text == falk_client_content

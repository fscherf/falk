import pytest


@pytest.mark.parametrize("interface", ["asgi", "wsgi"])
def test_middleware_headers(interface, start_falk_app):
    import requests

    def pre_component_middleware(get_response_header, set_response_header):
        # ensure that this middleware runs first
        if get_response_header("x-bar", ""):
            return

        set_response_header("x-foo", "foo")

    def post_component_middleware(get_response_header, set_response_header):
        # ensure that this middleware runs last
        if get_response_header("x-foo", ""):
            set_response_header("x-bar", "bar")

    def Index(set_response_body, set_response_status):
        set_response_status(418)
        set_response_body("I'm a teapot")

    def configure_app(
            mutable_app,
            add_route,
            add_pre_component_middleware,
            add_post_component_middleware,
    ):

        add_pre_component_middleware(pre_component_middleware)
        add_post_component_middleware(post_component_middleware)
        add_route("/", Index)

    mutable_app, base_url = start_falk_app(
        configure_app=configure_app,
        interface=interface,
    )

    response = requests.get(base_url)

    assert response.status_code == 418
    assert response.headers["X-Foo"] == "foo"
    assert response.headers["X-Bar"] == "bar"
    assert response.text == "I'm a teapot"


@pytest.mark.parametrize("interface", ["asgi", "wsgi"])
def test_middleware_responses(interface, start_falk_app):
    import requests

    def pre_component_middleware(
            request,
            set_response_status,
            set_response_body,
    ):

        if request["path"] != "/pre-component-middleware":
            return

        set_response_status(418)
        set_response_body("pre-component-middleware")

    def post_component_middleware(
            request,
            set_response_status,
            set_response_body,
    ):
        if request["path"] != "/post-component-middleware":
            return

        set_response_status(418)
        set_response_body("post-component-middleware")

    def Index(set_response_body, set_response_status):
        set_response_body("view")

    def configure_app(
            mutable_app,
            add_route,
            add_pre_component_middleware,
            add_post_component_middleware,
    ):

        add_pre_component_middleware(pre_component_middleware)
        add_post_component_middleware(post_component_middleware)
        add_route("/", Index)

    mutable_app, base_url = start_falk_app(
        configure_app=configure_app,
        interface=interface,
    )

    # pre component middleware
    response = requests.get(base_url + "/pre-component-middleware")

    assert response.status_code == 418
    assert response.text == "pre-component-middleware"

    # post component middleware
    response = requests.get(base_url + "/post-component-middleware")

    assert response.status_code == 418
    assert response.text == "post-component-middleware"

    # view
    response = requests.get(base_url)

    assert response.status_code == 200
    assert response.text == "view"

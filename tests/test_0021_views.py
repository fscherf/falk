import pytest


@pytest.mark.parametrize("interface", ["asgi", "wsgi"])
def test_responses(interface, start_falk_app):
    import requests

    def Index(
            request,
            set_response_header,
            set_response_body,
            set_response_status,
    ):

        set_response_header(
            "X-Foo", "foo",  # upper case
        )

        set_response_header(
            "x-bar", "bar",  # lower case
        )

        set_response_status(418)
        set_response_body("I'm a teapot")

    def configure_app(add_route):
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
def test_error_responses(interface, start_falk_app):
    import requests

    def Index():
        raise RuntimeError()

    def configure_app(add_route):
        add_route("/", Index)

    mutable_app, base_url = start_falk_app(
        configure_app=configure_app,
        interface=interface,
    )

    response = requests.get(base_url)

    assert response.status_code == 500

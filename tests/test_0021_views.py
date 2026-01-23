def test_responses(start_falk_app):
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
    )

    response = requests.get(base_url)

    assert response.status_code == 418
    assert response.headers["X-Foo"] == "foo"
    assert response.headers["X-Bar"] == "bar"
    assert response.text == "I'm a teapot"


def test_error_responses(start_falk_app):
    from falk.errors import BadRequestError, ForbiddenError, NotFoundError

    import requests

    def BadRequestErrorComponent():
        raise BadRequestError()

    def ForbiddenErrorComponent():
        raise ForbiddenError()

    def NotFoundErrorComponent():
        raise NotFoundError()

    def InternalServerErrorComponent():
        raise RuntimeError()

    def configure_app(add_route):
        add_route("/bad-request-error", BadRequestErrorComponent)
        add_route("/forbidden-error", ForbiddenErrorComponent)
        add_route("/not-found-error", NotFoundErrorComponent)
        add_route("/internal-server-error", InternalServerErrorComponent)

    mutable_app, base_url = start_falk_app(
        configure_app=configure_app,
    )

    # 400: Bad Request
    response = requests.get(base_url + "/bad-request-error")

    assert response.status_code == 400
    assert '<title>400 Bad Request</title>' in response.text
    assert '<h1>Error 400</h1>' in response.text
    assert '<p>Bad Request</p>' in response.text

    # 403: Forbidden
    response = requests.get(base_url + "/forbidden-error")

    assert response.status_code == 403
    assert '<title>403 Forbidden</title>' in response.text
    assert '<h1>Error 403</h1>' in response.text
    assert '<p>Forbidden</p>' in response.text

    # 404: Not Found (raised)
    response = requests.get(base_url + "/not-found-error")

    assert response.status_code == 404
    assert '<title>404 Not Found</title>' in response.text
    assert '<h1>Error 404</h1>' in response.text
    assert '<p>Not Found</p>' in response.text

    # 404: Not Found (unknown URL)
    response = requests.get(base_url + "/uknown-url")

    assert response.status_code == 404
    assert '<title>404 Not Found</title>' in response.text
    assert '<h1>Error 404</h1>' in response.text
    assert '<p>Not Found</p>' in response.text

    # 500: Internal Server Error
    response = requests.get(base_url + "/internal-server-error")

    assert response.status_code == 500
    assert '<title>500 Internal Server Error</title>' in response.text
    assert '<h1>Error 500</h1>' in response.text
    assert '<p>Internal Server Error</p>' in response.text

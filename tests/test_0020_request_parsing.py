import pytest


@pytest.mark.parametrize("interface", ["asgi", "wsgi"])
def test_request_parsing(interface, start_falk_app):
    import requests

    def Index(request, set_response_json):
        set_response_json(request._data)

    def configure_app(add_route):
        add_route("/", Index)

    mutable_app, base_url = start_falk_app(
        configure_app=configure_app,
        interface=interface,
    )

    # headers
    response = requests.get(
        base_url,
        headers={
            "X-Foo": "foo",  # upper case
            "x-bar": "bar",  # lower case
        },
    )

    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["headers"]["X-Foo"] == "foo"
    assert response_json["headers"]["X-Bar"] == "bar"

    # GET
    response = requests.get(base_url)
    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "GET"
    assert response_json["query"] == {}

    # GET: simple query
    response = requests.get(base_url + "?foo=bar")
    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "GET"
    assert response_json["query"] == {"foo": ["bar"]}

    # GET: multiple values for same key
    response = requests.get(base_url + "?foo=bar&foo=baz")
    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "GET"
    assert response_json["query"] == {"foo": ["bar", "baz"]}

    # GET: multiple keys with multiple values
    response = requests.get(base_url + "?foo=bar&foo=baz&bar=bar")
    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "GET"
    assert response_json["query"] == {"foo": ["bar", "baz"], "bar": ["bar"]}

    # POST
    response = requests.post(
        base_url,
        data={
            "foo": "bar",
        },
    )

    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "POST"
    assert response_json["json"] == {}
    assert response_json["post"] == {"foo": ["bar"]}

    # JSON POST
    response = requests.post(
        base_url,
        json={
            "foo": "bar",
        },
    )

    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "POST"
    assert response_json["json"] == {"foo": "bar"}
    assert response_json["post"] == {}

    # everything at once
    response = requests.post(
        base_url + "?foo=bar&foo=baz",
        headers={
            "X-Foo": "foo",  # upper case
            "x-bar": "bar",  # lower case
        },
        json={
            "bar": "foobar",
        },
    )

    status_code = response.status_code
    response_json = response.json()

    assert status_code == 200
    assert response_json["method"] == "POST"
    assert response_json["query"] == {"foo": ["bar", "baz"]}
    assert response_json["json"] == {"bar": "foobar"}
    assert response_json["post"] == {}

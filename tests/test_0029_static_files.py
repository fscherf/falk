def test_malicious_static_urls(start_falk_app):
    import requests

    def Index(set_response_body):
        set_response_body("Index")

    def configure_app(add_route):
        # If no routes are registered, falk always returns with the `It Works!`
        # page, which basically works as a catch-all.
        # In order to be able to check for 404 errors, we need at least
        # one route.

        add_route("/", Index)

    mutable_app, base_url, _ = start_falk_app(configure_app)

    uris = [
        "/static/falk/../../version.py",
        "/static/falk/%2e%2e/%2e%2e/version.py",
        "/static/../version.py",
        "/static/%2e%2e/version.py",
    ]

    for uri in uris:
        response = requests.get(base_url + uri)

        assert response.status_code == 404
        assert "__version__" not in response.text

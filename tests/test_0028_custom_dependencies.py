def test_custom_dependencies(start_falk_app):
    import requests

    def foo():
        return "foo"

    def foo2():
        return "bar"

    def Index(set_response_body, foo, bar):
        set_response_body(foo + bar)

    def configure_app(add_dependency, add_route):
        add_dependency(foo)
        add_dependency(foo2, name="bar")

        add_route("/", Index)

    _, base_url, _ = start_falk_app(
        configure_app=configure_app,
    )

    assert requests.get(base_url).text == "foobar"

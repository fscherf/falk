def test_asgi_sub_apps(start_falk_app):
    """
    This test tests mounting falk apps behind prefixes in other ASGI apps,
    by mounting the same falk app behind different prefixes into a starlette
    app and checking whether the ASGI `root_path` for every request is set
    correctly, and whether it is used correctly in reverse resolved URLs.
    """

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

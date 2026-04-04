def test_middleware_order(start_falk_app):
    """
    This test tests the order of execution of middlewares and components.
    """

    import requests

    def _run(
            caller_name,
            get_request_header,
            get_response_header,
            set_response_header,
            set_response_body,
    ):

        # run
        header = get_response_header("x-run", "")

        updated_header = ",".join([
            *[h for h in header.split(",") if h],
            caller_name,
        ])

        set_response_header("x-run", updated_header)

        # crash
        header = get_request_header("x-crash", "")

        if caller_name in header:
            raise RuntimeError(f"[crash in {caller_name}]")

        # finish
        header = get_request_header("x-finish", "[component]")

        if caller_name in header:
            set_response_body(caller_name)

    def pre_request_middleware(
            get_request_header,
            get_response_header,
            set_response_header,
            set_response_body,
    ):

        _run(
            caller_name="[pre_request_middleware]",
            get_request_header=get_request_header,
            get_response_header=get_response_header,
            set_response_header=set_response_header,
            set_response_body=set_response_body,
        )

    def pre_component_middleware(
            get_request_header,
            get_response_header,
            set_response_header,
            set_response_body,
    ):

        _run(
            caller_name="[pre_component_middleware]",
            get_request_header=get_request_header,
            get_response_header=get_response_header,
            set_response_header=set_response_header,
            set_response_body=set_response_body,
        )

    def post_component_middleware(
            get_request_header,
            get_response_header,
            set_response_header,
            set_response_body,
    ):

        _run(
            caller_name="[post_component_middleware]",
            get_request_header=get_request_header,
            get_response_header=get_response_header,
            set_response_header=set_response_header,
            set_response_body=set_response_body,
        )

    def post_request_middleware(
            get_request_header,
            get_response_header,
            set_response_header,
            set_response_body,
    ):

        _run(
            caller_name="[post_request_middleware]",
            get_request_header=get_request_header,
            get_response_header=get_response_header,
            set_response_header=set_response_header,
            set_response_body=set_response_body,
        )

    def Component(
            get_request_header,
            get_response_header,
            set_response_header,
            set_response_body,
    ):

        _run(
            caller_name="[component]",
            get_request_header=get_request_header,
            get_response_header=get_response_header,
            set_response_header=set_response_header,
            set_response_body=set_response_body,
        )

    def configure_app(
            set_setting,
            add_pre_request_middleware,
            add_pre_component_middleware,
            add_post_component_middleware,
            add_post_request_middleware,
            add_route,
    ):

        set_setting("debug", True)

        add_pre_request_middleware(pre_request_middleware)
        add_pre_component_middleware(pre_component_middleware)
        add_post_component_middleware(post_component_middleware)
        add_post_request_middleware(post_request_middleware)

        add_route("/", Component)

    mutable_app, base_url, _ = start_falk_app(
        configure_app=configure_app,
    )

    def request(crash="", finish=""):
        headers = {}

        if crash:
            headers["x-crash"] = crash

        if finish:
            headers["x-finish"] = finish

        return requests.get(
            base_url,
            headers=headers,
        )

    # normal execution
    response = request()

    assert response.status_code == 200
    assert response.headers["x-run"] == "[pre_request_middleware],[pre_component_middleware],[component],[post_component_middleware],[post_request_middleware]"  # NOQA
    assert response.text == "[component]"

    # finish in pre_request_middleware
    response = request(
        finish="[pre_request_middleware]",
    )

    assert response.status_code == 200
    assert response.headers["x-run"] == "[pre_request_middleware],[pre_component_middleware],[post_request_middleware]"  # NOQA
    assert response.text == "[pre_request_middleware]"

    # finish in pre_component_middleware
    response = request(
        finish="[pre_component_middleware]",
    )

    assert response.status_code == 200
    assert response.headers["x-run"] == "[pre_request_middleware],[pre_component_middleware],[post_request_middleware]"  # NOQA
    assert response.text == "[pre_component_middleware]"

    # crash in pre_request_middleware
    response = request(
        crash="[pre_request_middleware]",
    )

    assert response.status_code == 500
    assert response.headers["x-run"] == "[pre_request_middleware],[post_request_middleware]"  # NOQA
    assert "[crash in [pre_request_middleware]]" in response.text

    # crash in pre_component_middleware
    response = request(
        crash="[pre_component_middleware]",
    )

    assert response.status_code == 500
    assert response.headers["x-run"] == "[pre_request_middleware],[pre_component_middleware],[post_request_middleware]"  # NOQA
    assert "[crash in [pre_component_middleware]]" in response.text

    # crash in component
    response = request(
        crash="[component]",
    )

    assert response.status_code == 500
    assert response.headers["x-run"] == "[pre_request_middleware],[pre_component_middleware],[component],[post_request_middleware]"  # NOQA
    assert "[crash in [component]]" in response.text

    # crash in component and post_request_middleware
    response = request(
        crash="[component],[post_request_middleware]",
    )

    assert response.status_code == 500
    assert response.headers["x-run"] == "[pre_request_middleware],[pre_component_middleware],[component],[post_request_middleware]"  # NOQA
    assert "[crash in [post_request_middleware]]" in response.text


def test_middleware_headers(start_falk_app):
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

    mutable_app, base_url, _ = start_falk_app(
        configure_app=configure_app,
    )

    response = requests.get(base_url)

    assert response.status_code == 418
    assert response.headers["X-Foo"] == "foo"
    assert response.headers["X-Bar"] == "bar"
    assert response.text == "I'm a teapot"


def test_middleware_responses(start_falk_app):
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
        add_route("/<path:.*>", Index)

    mutable_app, base_url, _ = start_falk_app(
        configure_app=configure_app,
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

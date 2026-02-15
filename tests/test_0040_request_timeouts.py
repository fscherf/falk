import pytest


@pytest.mark.parametrize("websockets", [True, False])
def test_request_timeouts(websockets, page, start_falk_app):
    from test_app.app import configure_app

    def _configure_app(mutable_app, add_route, add_static_dir, settings):
        # FIXME: this is a hack! We need to do that because we want to use
        # the test app here, but there is no way to easily enable or
        # disable websockets.
        settings["websockets"] = websockets

        return configure_app(mutable_app, add_route, add_static_dir, settings)

    def rerender(index):
        page.click(f"#timeout-component-{index+1} button")

    def assert_component_message(index, text):
        assert page.wait_for_selector(
            f"#timeout-component-{index+1} .message:text('{text}')",
            timeout=5000,  # 5 seconds
        )

    def assert_log(text):
        assert page.inner_text("#event-log") == text

    def clear_log():
        page.click("#clear-event-log")
        assert_log("")

    _, base_url, stop_falk_app = start_falk_app(configure_app)
    url = base_url + "/client/timeouts"

    page.goto(url)
    page.wait_for_selector("h2:text('Timeouts')")

    # intial state
    assert_log("")

    assert_component_message(0, "initial render")
    assert_component_message(1, "initial render")
    assert_component_message(2, "initial render")
    assert_component_message(3, "initial render")
    assert_component_message(4, "initial render")

    # rerender first component
    clear_log()
    rerender(0)

    assert_component_message(0, "waiting")
    assert_component_message(0, "response late")
    assert_component_message(0, "rerender")

    assert_log(
        "timeout-component-1: beforerequest\ntimeout-component-1: response\n",
    )

    # rerender second component
    clear_log()
    rerender(1)

    assert_component_message(1, "waiting")
    assert_component_message(1, "response late")
    assert_component_message(1, "rerender")

    assert_log(
        "timeout-component-2: beforerequest\ntimeout-component-2: response\n",
    )

    # rerender third component with stopped server
    stop_falk_app()
    clear_log()
    rerender(2)

    assert_component_message(2, "waiting")
    assert_component_message(2, "response late")
    assert_component_message(2, "response timeout")

    assert_log("timeout-component-3: beforerequest\n")

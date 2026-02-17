def test_render_events(page, start_falk_app):
    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url, _ = start_falk_app(configure_app)

    url = base_url + "/client/render-events/"

    def assert_events(index, event_string):
        locator = page.locator(f"#component-{index+1} .events")

        expect(locator).to_have_text(event_string)

    def render(index):
        page.click(
            f"#component-{index+1} button.render",
        )

    def unmount(index):
        page.click(
            f"#component-{index+1} button.unmount",
        )

    page.goto(url)
    page.wait_for_selector("h2:text('Render Events')")

    # initial render
    assert_events(0, "initialRender,render")
    assert_events(1, "initialRender,render")
    assert_events(2, "initialRender,render")

    # render
    # click on "Render" of the first component
    render(0)

    assert_events(0, "initialRender,render,beforeRequest,response,render")
    assert_events(1, "initialRender,render")
    assert_events(2, "initialRender,render")

    # click on "Render" of the second component
    render(1)

    assert_events(0, "initialRender,render,beforeRequest,response,render")
    assert_events(1, "initialRender,render,beforeRequest,response,render")
    assert_events(2, "initialRender,render")

    # click on "Render" of the third component
    render(2)

    assert_events(0, "initialRender,render,beforeRequest,response,render")
    assert_events(1, "initialRender,render,beforeRequest,response,render")
    assert_events(2, "initialRender,render,beforeRequest,response,render")

    # unmount
    # click on "Unmount" of the first component
    unmount(0)

    assert_events(0, "initialRender,render,beforeRequest,response,render,unmount")  # NOQA
    assert_events(1, "initialRender,render,beforeRequest,response,render,unmount,initialRender,render")  # NOQA
    assert_events(2, "initialRender,render,beforeRequest,response,render,unmount,initialRender,render")  # NOQA

    # click on "Unmount" of the second component
    unmount(1)

    assert_events(0, "initialRender,render,beforeRequest,response,render,unmount")  # NOQA
    assert_events(1, "initialRender,render,beforeRequest,response,render,unmount,initialRender,render,unmount")  # NOQA
    assert_events(2, "initialRender,render,beforeRequest,response,render,unmount,initialRender,render,unmount,initialRender,render")  # NOQA

    # click on "Unmount" of the third component
    unmount(2)

    assert_events(0, "initialRender,render,beforeRequest,response,render,unmount")  # NOQA
    assert_events(1, "initialRender,render,beforeRequest,response,render,unmount,initialRender,render,unmount")  # NOQA
    assert_events(2, "initialRender,render,beforeRequest,response,render,unmount,initialRender,render,unmount,initialRender,render,unmount")  # NOQA


def test_recursive_umount_events(page, start_falk_app):
    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url, _ = start_falk_app(configure_app)

    url = base_url + "/client/render-events/"

    page.goto(url)
    page.wait_for_selector("h2:text('Render Events')")

    def assert_events(event_string):
        locator = page.locator("#recursive-unmount-log")

        expect(locator).to_have_text(event_string)

    # initially, no events should be logged
    assert_events("")

    # click "Unmount"
    page.click("#recursive-unmount")

    # all components should unmount recursively, inside-out
    assert_events("unmount-test-component-3,unmount-test-component-2,unmount-test-component-1")  # NOQA


def test_component_replacing(page, start_falk_app):
    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url, _ = start_falk_app(configure_app)

    url = base_url + "/client/render-events/"

    page.goto(url)
    page.wait_for_selector("h2:text('Render Events')")

    def assert_events(event_string):
        locator = page.locator("#replace-log")

        expect(locator).to_have_text(event_string)

    # initially, component 1 should be rendered
    assert_events("component 1: initialRender\n")

    # replace with component 2
    page.click("#replace-with-component-2")
    page.wait_for_selector("h3:text('Component 2')")
    assert_events("component 1: initialRender\ncomponent 1: unmount\ncomponent 2: initialRender\n")  # NOQA

    # replace with component 1
    page.click("#replace-with-component-1")
    page.wait_for_selector("h3:text('Component 1')")
    assert_events("component 1: initialRender\ncomponent 1: unmount\ncomponent 2: initialRender\ncomponent 2: unmount\ncomponent 1: initialRender\n")  # NOQA

def test_render_events(page, start_falk_app):
    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url = start_falk_app(configure_app)

    url = base_url + "/client/render-events/"

    def assert_events(index, event_string):
        locator = page.locator(f"#component-{index+1} .events")

        expect(locator).to_have_text(event_string)

    def render(index):
        page.click(
            f"#component-{index+1} button.render",
        )

    page.goto(url)
    page.wait_for_selector("h2:text('Render Events')")

    # initial render
    assert_events(0, "initialRender,render")
    assert_events(1, "initialRender,render")
    assert_events(2, "initialRender,render")

    # click on "Render" of the first component
    render(0)

    assert_events(0, "beforeRequest")
    assert_events(0, "render")

    assert_events(1, "initialRender,render")
    assert_events(2, "initialRender,render")

    # click on "Render" of the second component
    render(1)

    assert_events(0, "render")

    assert_events(1, "beforeRequest")
    assert_events(1, "render")

    assert_events(2, "initialRender,render")

    # click on "Render" of the third component
    render(2)

    assert_events(0, "render")
    assert_events(1, "render")

    assert_events(2, "beforeRequest")
    assert_events(2, "render")

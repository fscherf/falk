def test_event_delegation(page, start_falk_app):
    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url = start_falk_app(configure_app)

    url = base_url + "/client/event-delegation/"

    def assert_events(index, event_string):
        locator = page.locator(f"#component-{index+1} .events")

        expect(locator).to_have_text(event_string)

    def render(index):
        page.click(
            f"#component-{index+1} button.render",
        )

    # intial render
    page.goto(url)
    page.wait_for_selector("h2:text('Event Delegation')")

    assert_events(0, "falk.filterEvents:initialRender,falk.filterEvents:render")
    assert_events(1, "falk.on:initialRender,falk.on:render")
    assert_events(2, "")

    # click on "Render" of the first component
    render(0)

    assert_events(0, "falk.filterEvents:initialRender,falk.filterEvents:render,falk.filterEvents:beforeRequest")
    assert_events(0, "falk.filterEvents:render")

    assert_events(1, "falk.on:initialRender,falk.on:render")
    assert_events(2, "")

    # click on "Render" of the second component
    render(1)

    assert_events(0, "falk.filterEvents:render")

    assert_events(1, "falk.on:initialRender,falk.on:render,falk.on:beforeRequest")
    assert_events(1, "falk.on:render")

    assert_events(2, "")

    # click on "Render" of the third component
    render(2)

    assert_events(0, "falk.filterEvents:render")
    assert_events(1, "falk.on:render")
    assert_events(2, "")

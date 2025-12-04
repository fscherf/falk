def test_run_callback_in_javascript(page, start_falk_app):
    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url = start_falk_app(configure_app)

    url = base_url + "/client/run-callback-in-javascript/"

    def assert_counter_values(values):
        for index, value in enumerate(values):
            locator = page.locator(f"#counter-{index+1} span.state")

            expect(locator).to_have_text(str(value))

    def increment(index):
        page.click(
            f"#counter-{index+1} button.increment",
        )

    def decrement(index):
        page.click(
            f"#counter-{index+1} button.decrement",
        )

    page.goto(url)
    page.wait_for_selector("h2:text('runCallback in JavaScript')")

    # initial render
    assert_counter_values([0, 1, 2, 3, 4])

    # increment the first counter
    increment(0)
    assert_counter_values([1, 1, 2, 3, 4])

    # decrement the third counter
    decrement(2)
    assert_counter_values([1, 1, 1, 3, 4])

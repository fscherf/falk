def test_rendering_flags(page, start_falk_app):
    """
    This test uses `/rendering/rendering-flags` of the test app to test
    rendering skips and rendering enforcing.
    """

    import time

    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url = start_falk_app(configure_app)

    url = base_url + "/rendering/rendering-flags"

    def get_text(selector):
        return page.query_selector(selector).inner_text()

    def await_text(selector, text, negate=False):
        locator = page.locator(selector)

        if negate:
            expect(locator).not_to_have_text(text)

        else:
            expect(locator).to_have_text(text)

    def get_counter_states():
        return [
            get_text("#counter-1 .state"),
            get_text("#counter-2 .state"),
            get_text("#counter-3 .state"),
            get_text("#counter-4 .state"),
        ]

    def increment_counter(index):
        previous_value = int(get_text(f"#counter-{index+1} .state"))
        page.click(f"#counter-{index+1} .increment")
        await_text(f"#counter-{index+1} .state", str(previous_value+1))

    # initial render
    page.goto(url)

    page.wait_for_selector("h2:text('Rendering Flags')")

    assert get_counter_states() == ["1", "2", "3", "4"]

    # increment first counter to generate some non-initial state
    increment_counter(0)
    increment_counter(2)

    assert get_counter_states() == ["2", "2", "4", "4"]

    # rerender outer wrapper
    # the outer timestamp should change, the inner timestamp and the counter
    # states shouldn't
    outer_wrapper_timestamp = get_text("#outer-wrapper > .timestamp")
    inner_wrapper_timestamp = get_text("#inner-wrapper > .timestamp")

    page.click("#outer-wrapper > .render")

    await_text(
        "#outer-wrapper > .timestamp",
        outer_wrapper_timestamp,
        negate=True,
    )

    await_text(
        "#inner-wrapper > .timestamp",
        inner_wrapper_timestamp,
    )

    assert get_counter_states() == ["2", "2", "4", "4"]

    # rerender inner wrapper
    # only the inner timestamp should change
    outer_wrapper_timestamp = get_text("#outer-wrapper > .timestamp")
    inner_wrapper_timestamp = get_text("#inner-wrapper > .timestamp")

    page.click("#inner-wrapper > .render")

    await_text(
        "#outer-wrapper > .timestamp",
        outer_wrapper_timestamp,
    )

    await_text(
        "#inner-wrapper > .timestamp",
        inner_wrapper_timestamp,
        negate=True,
    )

    assert get_counter_states() == ["2", "2", "4", "4"]

    # skip rendering
    # nothing should happen
    outer_wrapper_timestamp = get_text("#outer-wrapper > .timestamp")
    inner_wrapper_timestamp = get_text("#inner-wrapper > .timestamp")

    page.click("#outer-wrapper > .skip-rendering")
    page.click("#inner-wrapper > .skip-rendering")

    # give the page some time to render
    time.sleep(2)

    await_text(
        "#outer-wrapper > .timestamp",
        outer_wrapper_timestamp,
    )

    await_text(
        "#inner-wrapper > .timestamp",
        inner_wrapper_timestamp,
    )

    assert get_counter_states() == ["2", "2", "4", "4"]

    # force rendering
    # the inner wrapper should disapear
    page.click("#outer-wrapper > .force-rendering")

    await_text("#outer-wrapper > .wrapper-component-body", "")

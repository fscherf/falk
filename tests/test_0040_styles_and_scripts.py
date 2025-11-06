import pytest


@pytest.mark.parametrize("url", [
    "/rendering/styles-and-scripts",
    "/rendering/code-splitting",
])
def test_styles_and_scripts(url, page, start_falk_app):
    """
    This test uses `/rendering/styles-and-scripts` and
    `/rendering/code-splitting` in the test-app to test
    whether loading external and inline styles and scripts work.

    To ensure that the falk client still works after we updated scripts in the
    browser, this test tries to increment a counter that is part of the test
    component, which uses the falk client to update its state.
    """

    import json

    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url = start_falk_app(configure_app)

    url = base_url + url

    # load page
    page.goto(url)
    page.wait_for_selector("h2")

    if "code-splitting" in url:
        # Initially the page should have loaded only one linked style and the
        # falk client script.
        assert len(page.query_selector_all("link")) == 1
        assert len(page.query_selector_all("style")) == 0
        assert len(page.query_selector_all("script")) == 1

        # load component
        page.click("button#load-component")
        page.wait_for_selector("h3:text('Component')")

    # When the component is loaded, we should see:
    #  - base.css as a linked style
    #  - falk.js as a linked script
    #  - Two additional linked styles
    #  - One additional inline styles
    #  - Two additional linked scripts
    #  - One additional inline scripts
    assert len(page.query_selector_all("link")) == 3
    assert len(page.query_selector_all("style")) == 1
    assert len(page.query_selector_all("script")) == 4

    # check if loaded styles and scripts got applied or executed correctly
    def await_css_content(selector, text):
        encoded_string = page.eval_on_selector(
            selector,
            "element => getComputedStyle(element, '::before').content",
        )

        assert json.loads(encoded_string) == text

    def await_text(selector, text):
        locator = page.locator(selector)

        expect(locator).to_have_text(text)

    # We need to us `get_css_content` here because both strings are set using
    # the `content` attribute in CSS. `element.inner_text()` would always yield
    # empty results.
    await_css_content(
        "div#component-app-external-style",
        "Loading app external styles works",
    )

    await_css_content(
        "div#component-package-external-style",
        "Loading package external styles works",
    )

    await_css_content(
        "div#component-inline-style",
        "Loading inline styles works",
    )

    await_text(
        "div#component-app-external-script",
        "Loading app external scripts works",
    )

    await_text(
        "div#component-package-external-script",
        "Loading package external scripts works",
    )

    await_text(
        "div#component-inline-script",
        "Loading inline scripts works",
    )

    # Ensure the falk client still works after we updated scripts by
    # incrementing a counter that is part of the test component
    await_text(".counter .state", "0")

    page.click('.counter .increment')

    await_text(".counter .state", "1")

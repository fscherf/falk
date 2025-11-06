def test_callback_passing(page, start_falk_app):
    """
    This test tests passing callbacks into child componont by using the test
    app `/client/callback-passing/`.
    """

    from playwright.sync_api import expect

    from test_app.app import configure_app

    _, base_url = start_falk_app(configure_app)

    url = base_url + "/client/callback-passing/"

    def reload():

        # make sure the page is truly unloaded by going to the index page first
        page.goto(base_url)
        page.wait_for_selector("h2:text('Index')")

        page.goto(url)
        page.wait_for_selector("h2:text('Callback Passing')")

    def await_text(name, text):
        locator = page.locator(f"#{name}-component-render-state")

        expect(locator).to_have_text(text)

    # initial load
    # both component should show "initial render"
    reload()

    await_text("outer", "initial render")
    await_text("inner", "initial render")

    # re render only the inner component
    # the outer component should be untouched
    page.click("#render-inner-component")

    await_text("outer", "initial render")
    await_text("inner", "re render")

    # re render outer component
    # the inner component should still show "initial render"
    reload()

    page.click("#render-outer-component")

    await_text("outer", "re render")
    await_text("inner", "initial render")

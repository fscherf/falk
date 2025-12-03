import pytest


@pytest.mark.parametrize("interface", ["asgi", "wsgi"])
def test_basic_component(interface, page, start_falk_app):
    """
    This test tests basic requests handling and partial re rendering by setting
    up a counter component that can be incremented if a button is clicked.

    The test is successful if:

      - The page shows a heading with the class name `title`
      - The component shows `1` as its initial value
      - The component shows `2` after it is clickd

      - The component changed its class name from `button-1` to `button-2`
        after it was clicked

    """

    from falk.components import HTML5Base

    def Counter(context, state, initial_render):
        if initial_render:
            state["counter"] = 1

        def increment():
            state["counter"] += 1

        context.update({
            "increment": increment,
        })

        return """
            <button
              id="button-{{ state.counter }}"
              onclick="{{ callback(increment) }}">

                {{ state.counter }}
            </button>
        """

    def Index(context, HTML5Base=HTML5Base, Counter=Counter):
        return """
            <HTML5Base title="Counter">
                <h1 id="title">Counter</h1>
                <Counter />
            </HTML5Base>
        """

    def configure_app(add_route):
        add_route(r"/", Index)

    _, base_url = start_falk_app(
        configure_app=configure_app,
        interface=interface,
    )

    # run test
    # go to the base URL and wait for the counter to appear
    page.goto(base_url)
    page.wait_for_selector("h1#title")
    page.wait_for_selector("#button-1")

    assert page.title() == "Counter"

    # increment counter
    assert page.inner_text("#button-1") == "1"

    page.click("#button-1")
    page.wait_for_selector("#button-2")

    assert page.inner_text("#button-2") == "2"

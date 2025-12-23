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


@pytest.mark.only_browser("chromium")
def test_prop_passing(page, start_falk_app):
    """
    This test tests whether passing all props of a component to another
    component works by defining three components: An outer component, a mid
    component and an inner component.
    The outer component calls the inner component with a prop, the mid
    component is forwarding all props it is given and the inner component
    is rendering the prop given by the outer component.

    The test does not use the HTML5Base component on purpose. This ensures
    that this rendering mechanism works without any client side hydration.

    The test is successful if the inner component gets rendered with the outer
    component text and attributes.

    """

    def InnerComponent(props):
        return """
            <div id="inner-component" foo="{{ props.foo }}">
                {{ props.children }}
            </div>
        """

    def MidComponent(props, InnerComponent=InnerComponent):
        return """
            <InnerComponent props="{{ props }}">
                {{ props.children }}
            </InnerComponent>
        """

    def OuterComponent(MidComponent=MidComponent):
        return """
            <MidComponent foo="bar">
                Outer Component Text
            </MidComponent>
        """

    def configure_app(add_route):
        add_route(r"/", OuterComponent)

    _, base_url = start_falk_app(
        configure_app=configure_app,
    )

    # run test
    page.goto(base_url)
    page.inner_text("#inner-component[foo=bar]") == "Outer Component Text"

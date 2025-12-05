from falk.wsgi import get_wsgi_app
from falk.asgi import get_asgi_app


def configure_app(add_route, add_static_dir):
    from test_app.components.rendering.styles_and_scripts import (
        StylesAndScripts,
        CodeSplitting,
    )

    from test_app.components.client.callback_passing import CallbackPassing
    from test_app.components.client.event_delegation import EventDelegation
    from test_app.components.client.render_events import RenderEvents
    from test_app.components.rendering.iframes import Iframes, Iframe
    from test_app.components.rendering.flags import RenderingFlags
    from test_app.components.events.render import Render
    from test_app.components.events.change import Change
    from test_app.components.events.submit import Submit
    from test_app.components.events.click import Click
    from test_app.components.events.input import Input
    from test_app.components.index import Index

    from test_app.components.client.run_callback_in_javascript import (
        RunCallbackInJavascript,
    )

    from test_app.components.client.run_callback_in_python import (
        RunCallbackInPython,
    )

    # static files
    add_static_dir("./static/")

    # routes: rendering
    add_route(
        r"/rendering/styles-and-scripts(/)",
        StylesAndScripts,
        name="rendering__styles_and_scripts",
    )

    add_route(
        r"/rendering/code-splitting(/)",
        CodeSplitting,
        name="rendering__code_splitting",
    )

    add_route(
        r"/rendering/rendering-flags(/)",
        RenderingFlags,
        name="rendering__flags",
    )

    add_route(
        r"/rendering/iframe/<index:\d+>(/)",
        Iframe,
        name="rendering__iframe",
    )

    add_route(
        r"/rendering/iframes(/)",
        Iframes,
        name="rendering__iframes",
    )

    # routes: events
    add_route(r"/events/render(/)", Render, name="events__render")
    add_route(r"/events/click(/)", Click, name="events__click")
    add_route(r"/events/input(/)", Input, name="events__input")
    add_route(r"/events/change(/)", Change, name="events__change")
    add_route(r"/events/submit(/)", Submit, name="events__submit")

    # routes: client
    add_route(
        r"/client/render-events(/)",
        RenderEvents,
        name="client__render_events",
    )

    add_route(
        r"/client/callback-passing(/)",
        CallbackPassing,
        name="client__callback_passing",
    )

    add_route(
        r"/client/event-delegation(/)",
        EventDelegation,
        name="client__event_delegation",
    )

    add_route(
        r"/client/run-callback-in-javascript(/)",
        RunCallbackInJavascript,
        name="client__run_callback_in_javascript",
    )

    add_route(
        r"/client/run-callback-in-python(/)",
        RunCallbackInPython,
        name="client__run_callback_in_python",
    )

    # routes: index
    add_route(r"/", Index, name="index")


wsgi_app = get_wsgi_app(configure_app, lazy=True)
asgi_app = get_asgi_app(configure_app)

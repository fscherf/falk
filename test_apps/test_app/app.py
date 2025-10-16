def configure_app(add_route, add_static_dir):
    from test_app.components.rendering.styles_and_scripts import (
        StylesAndScripts,
        CodeSplitting,
    )

    from test_app.components.rendering.iframes import Iframes, Iframe
    from test_app.components.events.render import Render
    from test_app.components.events.change import Change
    from test_app.components.events.submit import Submit
    from test_app.components.events.click import Click
    from test_app.components.events.input import Input

    from test_app.components.index import Index

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

    # routes: index
    add_route(r"/", Index, name="index")

from falk.components import HTML5Base
from falk.asgi import get_asgi_app


def Counter(initial_render, props, state, template_context):
    if initial_render:
        state.update({
            "count": props.get("initial_value", 0),
        })

    def increase():
        state["count"] += 1

    template_context.update({
        "increase": increase,
    })

    return """
        <div class="counter">
            <p>
                The button was clicked <strong>{{ state.count }}</strong> times
            </p>
            <button onclick="{{ falk.run_callback('increase') }}">
                Click Me!
            </button>
        </div>
    """


def HelloWorld(HTML5Base=HTML5Base, Counter=Counter):
    return """
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">

        <style>
            .hello-world {
                text-align: center;
            }
        </style>

        <HTML5Base title="Hello World">
            <main class="container hello-world">
                <h1>Hello World</h1>
                <Counter initial_value="{{ 0 }}" />
            </main>
        </HTML5Base>
    """


def configure_app(mutable_settings, add_route):
    mutable_settings["debug"] = True

    add_route("/", HelloWorld)


app = get_asgi_app(configure_app)

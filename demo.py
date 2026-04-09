from falk.components import HTML5Base
from falk.asgi import get_asgi_app


def Counter(initial_render, props, state, add_callback):

    # initialize state object
    if initial_render:
        state.update({
            "count": props.get("initial_value", 0),
        })

    # this callback gets called when the button is clicked
    # (callbacks can be sync or async)
    def increment(args):
        state["count"] += args[0]

    add_callback(increment)

    return """
        <button onclick="{{ falk.run_callback('increment', [1]) }}">
            Count: <strong>{{ state.count }}</strong>
        </button>
    """


def Index(HTML5Base=HTML5Base, Counter=Counter):
    return """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">

        <style>
            .container {
                margin: 0 auto;
                margin-top: 2em;
            }

            button {
                padding: 5px 10px;
                margin-bottom: 10px;
            }
        </style>

        <HTML5Base title="falk Hello World">
            <div class="container">
                <h1>falk Hello World</h1>

                {% for i in range(5) %}
                    <Counter initial_value="{{ i }}" />
                    <br/>
                {% endfor %}
            </div>
        </HTML5Base>
    """


def configure_app(set_setting, add_route):
    set_setting("debug", True)

    add_route("/", Index)


app = get_asgi_app(configure_app)

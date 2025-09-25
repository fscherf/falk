import datetime

from falk.components import HTML5Base


def Page(context, props):
    context.update({
        "HTML5Base": HTML5Base,
        "Counter": Counter,
    })

    return """
        <HTML5Base props="{{ props }}">
            <h1>falk Test App</h1>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/counters/">Counters</a></li>
                <li><a href="/clocks/">Clocks</a></li>
            </ul>
            {{ props.children }}
        </HTML5Base>
    """


def Index(context):
    context.update({
        "Page": Page,
    })

    return """
        <Page title="falk Test App">
            <h2>Index</h2>
        </Page>
    """


def Counter(context, state, initial_render, props):
    if initial_render:
        state.update({
            "count": props.get("initial_value", 0),
        })

    def decrement():
        state["count"] -= 1

    def increment():
        state["count"] += 1

    context.update({
        "decrement": decrement,
        "increment": increment,
    })

    return """
        <div>
            <button onclick="{{ callback(decrement) }}">-</button>
            <span>{{ state.count }}</span>
            <button onclick="{{ callback(increment) }}">+</button>
        </div>
    """


def Counters(context):
    context.update({
        "Page": Page,
        "Counter": Counter,
    })

    return """
        <Page title="falk Test App - Counter">
            <h1>Counters</h1>
            {% for i in range(5) %}
                <Counter initial_value="{{ i }}" />
            {% endfor %}
        </Page>
    """


def Clock(context, props, initial_render, state):
    if initial_render:
        state["refresh_rate"] = int(props.get("refresh_rate", 1000))

    context.update({
        "datetime": datetime,
    })

    return """
        <div onrender="{{ callback(render, delay=state['refresh_rate']) }}">
            {{ datetime.datetime.now() }} (refresh rate: {{ state.refresh_rate }})
        </div>
    """


def Clocks(context):
    context.update({
        "Page": Page,
        "Clock": Clock,
        "Counter": Counter,
    })

    return """
        <Page title="falk Test App - Clocks">
            <h1>Clocks</h1>
            <Clock refresh_rate=10000 />
            <Clock refresh_rate=5000 />
            <Clock />

            <h2>Counters</h2>
            <p>
                These are here to ensure that other callbacks don't interfere
                with periodically re rendering components.
            </p>
            <Counter />
            <Counter />
        </Page>
    """


def configure_app(add_route, app, settings):
    add_route(r"/counters/", Counters)
    add_route(r"/clocks/", Clocks)
    add_route(r"/", Index)

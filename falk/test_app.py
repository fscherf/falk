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


def configure_app(add_route, app, settings):
    add_route(r"/counters/", Counters)
    add_route(r"/", Index)

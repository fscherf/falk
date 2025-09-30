import datetime

from test_app.components.base import Base


def Clock(context, props, initial_render, state):
    if initial_render:
        state["refresh_rate"] = props.get("refresh_rate", 1000)
        state["initial"] = props.get("initial", False)

    context.update({
        "datetime": datetime,
    })

    return """
        <div onrender="{{ callback(render, delay=state['refresh_rate'], initial=state['initial']) }}">
            {{ datetime.datetime.now() }} (refresh rate: {{ state.refresh_rate }}, intitial: {{ state.initial}})
        </div>
    """


def Render(context):
    context.update({
        "Base": Base,
        "Clock": Clock,
    })

    return """
        <Base title="Render Events">
            <h2>Render Events</h2>

            <Clock initial="{{ True }}" />
            <Clock />
            <Clock refresh_rate="{{ 5000 }}" />
            <Clock refresh_rate="{{ 10000 }}" />
        </Base>
    """

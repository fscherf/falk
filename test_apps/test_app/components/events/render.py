import datetime

from test_app.components.base import Base


def Clock(context, props, initial_render, state):
    if initial_render:
        state["refresh_rate"] = props.get("refresh_rate", "1")

    context.update({
        "datetime": datetime,
    })

    return """
        <div onrender="{{ callback(render, delay=state['refresh_rate']) }}">
            {{ datetime.datetime.now() }} (refresh rate: {{ state.refresh_rate }})
        </div>
    """


def Render(Base=Base, Clock=Clock):
    return """
        <Base title="Render Events">
            <h2>Render Events</h2>

            <Clock />
            <Clock refresh_rate="5s" />
            <Clock refresh_rate="10s" />
        </Base>
    """

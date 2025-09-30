from test_app.components.base import Base


def Hover(context, state, initial_render):
    if initial_render:
        state["hovered"] = False

    def update(event):
        if event["type"] == "mouseover":
            state["hovered"] = True

        elif event["type"] == "mouseout":
            state["hovered"] = False

    context.update({
        "Base": Base,
        "update": update,
    })

    return """
        <Base title="Hover events">
            <h2>Hover Events</h2>
            <p>The text box should state in text when it is hovered</p>

            <span id="text-box"
              onMouseOver="{{ callback(update) }}"
              onMouseOut="{{ callback(update) }}">

                This text is {{ "not" if not state.hovered else "" }} hovered
            </span>
        </Base>
    """

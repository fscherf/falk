from test_app.components.base import Base


def Focus(context):
    context.update({
        "Base": Base,
    })

    return """
        <Base title="Focus Events">
            <h2>Focus Events</h2>
            <p>TODO</p>
        </Base>
    """

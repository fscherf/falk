from test_app.components.base import Base


def Index(context):
    context.update({
        "Base": Base,
    })

    return """
        <Base />
    """

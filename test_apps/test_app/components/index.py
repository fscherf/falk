from test_app.components.base import Base


def Index(context, Base=Base):
    context.update({
        "Base": Base,
    })

    return """
        <Base />
    """

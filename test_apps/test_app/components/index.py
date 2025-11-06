from test_app.components.base import Base


def Index(context, Base=Base):
    context.update({
        "Base": Base,
    })

    return """
        <Base title="Index">
            <h2>Index</h2>
        </Base>
    """

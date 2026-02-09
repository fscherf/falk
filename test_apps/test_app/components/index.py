from test_app.components.base import Base


def Index(template_context, Base=Base):
    template_context.update({
        "Base": Base,
    })

    return """
        <Base title="Index">
            <h2>Index</h2>
        </Base>
    """

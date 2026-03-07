from falk.components import HTML5Base
from falk.asgi import get_asgi_app


def HelloWorld(HTML5Base=HTML5Base):
    return """
        <HTML5Base title="Hello World">
            <h1>Hello World</h1>
        </HTML5Base>
    """


def configure_app(mutable_settings, add_route):
    mutable_settings["debug"] = True

    add_route("/", HelloWorld)


app = get_asgi_app(configure_app)

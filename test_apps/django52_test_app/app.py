from django52_test_app.asgi import application as django_asgi_app

from falk.contrib.django.auth import DjangoUserMiddleware
from falk.asgi import get_asgi_app

from django52_test_app.components.forms import DjangoFormComponent
from django52_test_app.components.auth import AuthComponent
from django52_test_app.components.errors import Forbidden
from django52_test_app.components.index import Index


def configure_app(mutable_settings, add_route, add_pre_component_middleware):
    mutable_settings["debug"] = True
    mutable_settings["forbidden_error_component"] = Forbidden

    add_pre_component_middleware(DjangoUserMiddleware)

    add_route(r"/forms(/)", DjangoFormComponent)
    add_route(r"/auth(/)", AuthComponent)
    add_route(r"/", Index)


falk_asgi_app = get_asgi_app(configure_app)


async def asgi_app(scope, receive, send):
    # TODO: This poor-mans routing would not be necessary if we had an ASGI
    # container component of some sort that could be used with `add_route`.

    django_prefixes = (
        "/_django/",
        "/admin",
    )

    for prefix in django_prefixes:
        if scope["path"].startswith(prefix):
            return await django_asgi_app(scope, receive, send)

    return await falk_asgi_app(scope, receive, send)

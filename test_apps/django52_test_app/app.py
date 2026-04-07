from django52_test_app.asgi import application as django_asgi_app

from falk.contrib.django.auth import DjangoUserMiddleware
from falk.asgi import get_asgi_app, Mount

from django52_test_app.components.forms import DjangoFormComponent
from django52_test_app.components.auth import AuthComponent
from django52_test_app.components.errors import Forbidden
from django52_test_app.components.index import Index


def configure_app(mutable_settings, add_route, add_pre_component_middleware):
    mutable_settings["debug"] = True
    mutable_settings["forbidden_error_component"] = Forbidden

    add_pre_component_middleware(DjangoUserMiddleware)

    add_route(r"/_django/<path:.*>", Mount(django_asgi_app, lifespan=False))
    add_route(r"/admin/<path:.*>", Mount(django_asgi_app, lifespan=False))

    add_route(r"/forms(/)", DjangoFormComponent)
    add_route(r"/auth(/)", AuthComponent)
    add_route(r"/", Index)


asgi_app = get_asgi_app(configure_app)

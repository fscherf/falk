import os

from falk.dependency_injection import run_callback, run_coroutine_sync
from falk.providers.routing import add_route_provider
from falk.tokens import encode_token, decode_token
from falk.request_handling import handle_request
from falk.components import Error404, Error500
from falk.keys import get_random_key
from falk.html import get_node_id

from falk.component_caching import (
    get_component_id,
    cache_component,
    get_component,
)

from falk.providers.requests import (
    get_request_header_provider,
    set_request_header_provider,
    del_request_header_provider,
)

from falk.providers.responses import (
    set_response_status_provider,
    get_response_header_provider,
    set_response_header_provider,
    del_response_header_provider,
)


def get_default_app():
    app = {
        "settings": {
            "run_coroutine_sync": run_coroutine_sync,
        },
        "entry_points": {
            "handle_request": handle_request,
        },
        "component_cache": {},
        "routes": [],
    }

    # settings: tokens
    if "FALK_TOKEN_KEY" in os.environ:
        token_key = os.environ["FALK_TOKEN_KEY"]

    else:
        token_key = get_random_key()

    app["settings"].update({
        "token_key": token_key,
        "encode_token": encode_token,
        "decode_token": decode_token,
    })

    # settings: components
    app["settings"].update({
        "node_id_random_bytes": 8,
        "get_node_id": get_node_id,
    })

    # settings: error components
    app["settings"].update({
        "error_404_component": Error404,
        "error_500_component": Error500,
    })

    # settings: component caching
    if "FALK_COMPONENT_ID_SALT" in os.environ:
        component_id_salt = os.environ["FALK_COMPONENT_ID_SALT"]

    else:
        component_id_salt = get_random_key()

    app["settings"].update({
        "component_id_salt": component_id_salt,
        "get_component_id": get_component_id,
        "cache_component": cache_component,
        "get_component": get_component,
    })

    # settings: dependencies
    app["settings"].update({
        "providers": {
            "set_response_status": set_response_status_provider,
            "get_request_header": get_request_header_provider,
            "set_request_header": set_request_header_provider,
            "del_request_header": del_request_header_provider,
            "get_response_header": get_response_header_provider,
            "set_response_header": set_response_header_provider,
            "del_response_header": del_response_header_provider,
        },
    })

    return app


def run_configure_app(configure_app):
    app = get_default_app()

    run_callback(
        callback=configure_app,
        dependencies={
            "app": app,
            "settings": app["settings"],
            "routes": app["routes"],
        },
        providers={
            "add_route": add_route_provider,
        },
    )

    return app

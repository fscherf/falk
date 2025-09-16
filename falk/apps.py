import os

from falk.dependency_injection import run_callback, run_coroutine_sync
from falk.providers.routing import add_route_provider
from falk.immutable_proxy import get_immutable_proxy
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

from falk.providers.middlewares import (
    add_post_component_middleware_provider,
    add_pre_component_middleware_provider,
)

from falk.providers.responses import (
    set_response_status_provider,
    get_response_header_provider,
    set_response_header_provider,
    del_response_header_provider,
    set_response_content_type_provider,
    set_response_body_provider,
    set_response_file_provider,
    set_response_json_provider,
)


def get_default_app():
    mutable_app = {
        "settings": {
            "run_coroutine_sync": run_coroutine_sync,
        },
        "entry_points": {
            "handle_request": handle_request,
        },
        "component_cache": {},
        "routes": [],
    }

    # settings: middlewares
    mutable_app["settings"].update({
        "pre_component_middlewares": [],
        "post_component_middlewares": [],
    })

    # settings: tokens
    if "FALK_TOKEN_KEY" in os.environ:
        token_key = os.environ["FALK_TOKEN_KEY"]

    else:
        token_key = get_random_key()

    mutable_app["settings"].update({
        "token_key": token_key,
        "encode_token": encode_token,
        "decode_token": decode_token,
    })

    # settings: components
    mutable_app["settings"].update({
        "node_id_random_bytes": 8,
        "get_node_id": get_node_id,
    })

    # settings: error components
    mutable_app["settings"].update({
        "error_404_component": Error404,
        "error_500_component": Error500,
    })

    # settings: component caching
    if "FALK_COMPONENT_ID_SALT" in os.environ:
        component_id_salt = os.environ["FALK_COMPONENT_ID_SALT"]

    else:
        component_id_salt = get_random_key()

    mutable_app["settings"].update({
        "component_id_salt": component_id_salt,
        "get_component_id": get_component_id,
        "cache_component": cache_component,
        "get_component": get_component,
    })

    # settings: dependencies
    mutable_app["settings"].update({
        "providers": {
            "set_response_status": set_response_status_provider,
            "get_request_header": get_request_header_provider,
            "set_request_header": set_request_header_provider,
            "del_request_header": del_request_header_provider,
            "get_response_header": get_response_header_provider,
            "set_response_header": set_response_header_provider,
            "del_response_header": del_response_header_provider,
            "set_response_content_type": set_response_content_type_provider,
            "set_response_body": set_response_body_provider,
            "set_response_file": set_response_file_provider,
            "set_response_json": set_response_json_provider,
        },
    })

    return mutable_app


def run_configure_app(configure_app):
    mutable_app = get_default_app()

    run_callback(
        callback=configure_app,
        dependencies={
            # meta data
            "caller": configure_app,

            # immutable
            "app": get_immutable_proxy(
                data=mutable_app,
                name="app",
                mutable_version_name="mutable_app",
            ),

            "settings": get_immutable_proxy(
                data=mutable_app["settings"],
                name="settings",
                mutable_version_name="mutable_settings",
            ),

            # explicitly mutable
            "mutable_app": mutable_app,
            "mutable_settings": mutable_app["settings"],
        },
        providers={
            "add_route": add_route_provider,

            "add_pre_component_middleware":
                add_pre_component_middleware_provider,

            "add_post_component_middleware":
                add_post_component_middleware_provider,
        },
    )

    return mutable_app

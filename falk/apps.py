import os

from falk.providers.routing import add_route_provider, get_url_provider
from falk.dependency_injection import run_callback, run_coroutine_sync
from falk.providers.static_files import add_static_dir_provider
from falk.middlewares.static_files import serve_static_files
from falk.utils.environment import get_boolean, get_integer
from falk.providers.callbacks import run_callback_provider
from falk.immutable_proxy import get_immutable_proxy
from falk.tokens import encode_token, decode_token
from falk.static_files import get_falk_static_dir
from falk.request_handling import handle_request
from falk.extra_template_context import get_url
from falk.components import Error404, Error500
from falk.node_ids import get_node_id
from falk.hashing import get_md5_hash
from falk.keys import get_random_key

from falk.component_registry import (
    register_component,
    get_component_id,
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

from falk.providers.flags import (
    force_rendering_provider,
    skip_rendering_provider,
)


def get_default_app():
    mutable_app = {
        "settings": {
            "workers": get_integer("FALK_WORKERS", 4),
            "run_coroutine_sync": run_coroutine_sync,
            "hash_string": get_md5_hash,
            "websockets": get_boolean("FALK_WEBSOCKETS", True),
        },
        "entry_points": {
            "handle_request": handle_request,
            "on_startup": lambda mutable_app: None,
            "on_shutdown": lambda mutable_app: None,
        },
        "executor": None,
        "components": {},
        "routes": [],
    }

    # settings: middlewares
    mutable_app["settings"].update({
        "pre_component_middlewares": [
            serve_static_files,
        ],
        "post_component_middlewares": [],
    })

    # settings: static files
    mutable_app["settings"].update({
        "static_url_prefix": "/static/",
        "static_dirs": [
            get_falk_static_dir(),
        ],
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

    # settings: component registry
    if "FALK_COMPONENT_ID_SALT" in os.environ:
        component_id_salt = os.environ["FALK_COMPONENT_ID_SALT"]

    else:
        component_id_salt = get_random_key()

    mutable_app["settings"].update({
        "component_id_salt": component_id_salt,
        "get_component_id": get_component_id,
        "register_component": register_component,
        "get_component": get_component,
    })

    # settings: dependencies
    mutable_app["settings"].update({
        "providers": {
            "skip_rendering": skip_rendering_provider,
            "force_rendering": force_rendering_provider,
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
            "run_callback": run_callback_provider,
            "get_url": get_url_provider,
        },
    })

    # settings: templating
    mutable_app["settings"].update({
        "extra_template_context": {
            "get_url": get_url,
        },
    })

    return mutable_app


def run_configure_app(configure_app):
    mutable_app = get_default_app()

    # run user `configure_app` callback
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
            "add_static_dir": add_static_dir_provider,
            "get_url": get_url_provider,

            "add_pre_component_middleware":
                add_pre_component_middleware_provider,

            "add_post_component_middleware":
                add_post_component_middleware_provider,
        },
    )

    # setup component registry
    for route in mutable_app["routes"]:
        mutable_app["settings"]["register_component"](
            component=route[1],
            mutable_app=mutable_app,
        )

    return mutable_app

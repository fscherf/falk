import os

from falk.tokens import encode_token, decode_token
from falk.keys import get_random_key

from falk.component_caching import (
    get_component_id,
    cache_component,
    get_component,
)


def get_default_app():
    app = {
        "settings": {},
        "entry_points": {},
        "component_cache": {},
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

    return app

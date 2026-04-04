import logging

KEYS = [

    # core
    "debug",
    "workers",
    "run_coroutine_sync",
    "hash_string",
    "websockets",
    "default_file_upload_handler",

    # static files
    "static_url_prefix",

    # tokens
    "token_secret",
    "encode_token",
    "decode_token",

    # components
    "node_id_random_bytes",
    "get_node_id",

    # error components
    "bad_request_error_component",
    "forbidden_error_component",
    "not_found_error_component",
    "internal_server_error_component",

    # component registry
    "get_component_id",
    "register_component",
    "get_component",
    "get_file_upload_handler",

    # templating
    "extra_template_context",
]

logger = logging.getLogger("falk.settings")


def _check_key(key):
    if key not in KEYS:
        raise ValueError(
            f"Unknown settings key '{key}'. Available keys: {', '.join(KEYS)}",
        )


def _check_value(mutable_settings, key, value):
    original_type = type(mutable_settings[key])
    new_type = type(value)

    if new_type == original_type:
        return

    logger.warning(
        "settings.%s was set to %s which is %s instead of %s",
        key,
        repr(value),
        new_type.__name__,
        original_type.__name__,
    )


def get_setting_provider(mutable_settings):
    # TODO: add tests

    def get_setting(key):
        _check_key(key)

        return mutable_settings[key]

    return get_setting


def set_setting_provider(mutable_settings):
    # TODO: add tests

    def set_setting(key, value):
        _check_key(key)
        _check_value(mutable_settings, key, value)

        mutable_settings[key] = value

    return set_setting

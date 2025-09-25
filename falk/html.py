import secrets
import base64

from falk.errors import InvalidSettingsError


def get_node_id(mutable_app):
    if "node_id_random_bytes" not in mutable_app["settings"]:
        raise InvalidSettingsError(
            "'node_id_random_bytes' needs to be configured to generate node ids",  # NOQA
        )

    random_bytes = mutable_app["settings"]["node_id_random_bytes"]
    token_bytes = secrets.token_bytes(random_bytes)
    random_id = base64.urlsafe_b64encode(token_bytes).rstrip(b"=").decode()

    # The IDs get used as CSS selectors and CSS selectors can not start with
    # a number. To ensure this never happens, we prefix every ID with an
    # uppercase `F`.
    random_id = "F" + random_id

    return random_id

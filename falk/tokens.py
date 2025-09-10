import hashlib
import base64
import hmac
import json

from falk.errors import InvalidSettingsError, InvalidTokenError


def encode_token(component_id, component_state, mutable_app):
    if "token_key" not in mutable_app["settings"]:
        raise InvalidSettingsError(
            "'token_key' needs to be configured to encode tokens",
        )

    key = mutable_app["settings"]["token_key"]

    component_data = json.dumps(
        [component_id, component_state],
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    signature = hmac.new(
        key=key.encode(),
        msg=component_data,
        digestmod=hashlib.sha256,
    )

    payload = signature.digest() + component_data
    token = base64.urlsafe_b64encode(payload).decode()

    return token


def decode_token(token, mutable_app):
    if "token_key" not in mutable_app["settings"]:
        raise InvalidSettingsError(
            "'token_key' needs to be configured to decode tokens",
        )

    key = mutable_app["settings"]["token_key"]

    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        signature = decoded[:32]
        component_data = decoded[32:]

    except Exception as exception:
        raise InvalidTokenError() from exception

    expected_signature = hmac.new(
        key=key.encode(),
        msg=component_data,
        digestmod=hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(signature, expected_signature):
        raise InvalidTokenError()

    component_id, component_state = json.loads(
        component_data.decode(),
    )

    return component_id, component_state

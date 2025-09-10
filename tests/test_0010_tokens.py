import pytest


def test_state_encoding_and_decoding():
    from falk.tokens import decode_token, encode_token
    from falk.errors import InvalidTokenError
    from falk.apps import get_default_app
    from falk.keys import get_random_key

    app = get_default_app()

    app["settings"]["token_key"] = get_random_key()
    component_id = "foo.bar.baz"

    component_state = {
        "foo": "bar",
        "bar": "baz",
        "baz": [1, 2, 3],
    }

    token = encode_token(
        component_id=component_id,
        component_state=component_state,
        mutable_app=app,
    )

    # valid key
    _component_identifier, _component_state = decode_token(
        token=token,
        mutable_app=app,
    )

    assert _component_identifier == component_id
    assert _component_state == component_state

    # invalid key
    app["settings"]["token_key"] = "invalid-key"

    with pytest.raises(InvalidTokenError):
        decode_token(
            token=token,
            mutable_app=app,
        )


def test_invalid_tokens():
    from falk.errors import InvalidTokenError
    from falk.apps import get_default_app
    from falk.tokens import decode_token
    from falk.keys import get_random_key

    app = get_default_app()

    with pytest.raises(InvalidTokenError):
        decode_token(
            token="foo",
            mutable_app=app,
        )


def test_tampered_with_tokens():
    import base64
    import json

    from falk.tokens import decode_token, encode_token
    from falk.errors import InvalidTokenError
    from falk.apps import get_default_app
    from falk.keys import get_random_key

    app = get_default_app()
    component_id = "foo.bar.baz"

    component_state = {
        "foo": "bar",
        "bar": "baz",
        "baz": [1, 2, 3],
    }

    def unpack(token):
        decoded = base64.urlsafe_b64decode(token.encode())
        signature = decoded[:32]
        component_data = decoded[32:]

        component_id, component_state = json.loads(
            component_data.decode(),
        )

        return component_id, component_state, signature

    def pack(component_id, component_state, signature):
        component_data = json.dumps(
            [component_id, component_state],
            separators=(",", ":"),
            sort_keys=True,
        ).encode()

        payload = signature + component_data
        token = base64.urlsafe_b64encode(payload).decode()

        return token

    token = encode_token(
        component_id=component_id,
        component_state=component_state,
        mutable_app=app,
    )

    # test unpack and pack
    assert decode_token(token=token, mutable_app=app)

    _component_id, _component_state, _signature = unpack(token)
    _token = pack(_component_id, _component_state, _signature)

    assert decode_token(token=_token, mutable_app=app)

    # test changed component identifier
    _component_id, _component_state, _signature = unpack(token)
    _token = pack("changed", _component_state, _signature)

    with pytest.raises(InvalidTokenError):
        decode_token(
            token=_token,
            mutable_app=app,
        )

    # test changed component state
    _component_id, _component_state, _signature = unpack(token)
    _component_state["changed"] = "changed"
    _token = pack(_component_id, _component_state, _signature)

    with pytest.raises(InvalidTokenError):
        decode_token(
            token=_token,
            mutable_app=app,
        )


def test_invalid_settings_errors():
    from falk.tokens import decode_token, encode_token
    from falk.errors import InvalidSettingsError
    from falk.apps import get_default_app

    with pytest.raises(InvalidSettingsError):
        encode_token(
            component_id="foo.bar.baz",
            component_state={},
            mutable_app={
                "settings": {},
            },
        )

    with pytest.raises(InvalidSettingsError):
        decode_token(
            token="foo",
            mutable_app={
                "settings": {},
            },
        )

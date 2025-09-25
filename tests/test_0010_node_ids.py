import pytest


def test_get_node_id():
    from falk.errors import InvalidSettingsError
    from falk.node_ids import get_node_id
    from falk.apps import get_default_app

    app = get_default_app()

    app["settings"]["node_id_random_bytes"] = 8

    random_id1 = get_node_id(mutable_app=app)
    random_id2 = get_node_id(mutable_app=app)

    app["settings"]["node_id_random_bytes"] = 12

    random_id3 = get_node_id(mutable_app=app)
    random_id4 = get_node_id(mutable_app=app)

    assert len(random_id1) == 12
    assert len(random_id3) == 17
    assert random_id1 != random_id2 != random_id3 != random_id4

    # invalid settings
    with pytest.raises(InvalidSettingsError):
        get_node_id(mutable_app={"settings": {}})

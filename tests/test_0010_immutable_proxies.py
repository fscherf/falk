import pytest


def test_immutable_proxies():
    from falk.immutable_proxy import get_immutable_proxy

    mutable_data = {
        "foo": ["bar", "baz"],
        "bar": {
            "foobar": "bazbar",
        },
    }

    immutable_data = get_immutable_proxy(mutable_data)

    # dict
    assert list(immutable_data.keys()) == ["foo", "bar"]
    assert "foo" in immutable_data
    assert "baz" not in immutable_data

    with pytest.raises(TypeError):
        immutable_data["foo"] = "baz"

    with pytest.raises(TypeError):
        immutable_data["new-key"] = "foo"

    with pytest.raises(TypeError):
        immutable_data.update({
            "new-key": "foo",
        })

    # list
    assert len(immutable_data["foo"]) == 2
    assert "bar" in immutable_data["foo"]
    assert "foo" not in immutable_data["foo"]

    with pytest.raises(TypeError):
        immutable_data["foo"].append("foo")

    with pytest.raises(TypeError):
        immutable_data["foo"].insert(0, "foo")

    with pytest.raises(TypeError):
        immutable_data["foo"].extend(["foo"])

    with pytest.raises(TypeError):
        immutable_data["foo"] += ["foo"]

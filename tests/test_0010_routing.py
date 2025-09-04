import pytest


def test_routing():
    from falk.routing import get_component, get_route, get_url

    from falk.errors import (
        InvalidRouteArgsError,
        InvalidRouteError,
        UnknownRouteError,
        InvalidPathError,
    )

    def ShowModel():
        pass

    def ShowModelObject():
        pass

    def AdminIndex():
        pass

    def PageIndex():
        pass

    routes = [
        get_route(
            r"/admin/<model>/<pk:\d+>(/)",
            ShowModelObject,
            name="show_model_object",
        ),

        get_route(
            r"/admin/<model>(/)",
            ShowModel,
            name="show_model",
        ),

        get_route(  # non optional trailing slash
            r"/admin/",
            AdminIndex,
            name="admin_index",
        ),

        get_route(  # unnamed route
            r"/",
            PageIndex,
        ),
    ]

    # get_route: invalid route
    with pytest.raises(InvalidRouteError):
        get_route(
            r"admin/",
            AdminIndex,
        )

    # get_component: invalid path
    with pytest.raises(InvalidPathError):
        assert get_component(
            routes,
            "admin/",
        )

    # get_component: trailing slash
    assert get_component(
        routes,
        "/admin/users/10/",
    ) == (
        ShowModelObject,
        {
            "model": "users",
            "pk": "10",
        },
    )

    assert get_component(
        routes,
        "/admin/users/",
    ) == (
        ShowModel,
        {
            "model": "users",
        },
    )

    # get_component: no trailing slash
    assert get_component(
        routes,
        "/admin/users/10",
    ) == (
        ShowModelObject,
        {
            "model": "users",
            "pk": "10",
        },
    )

    assert get_component(
        routes,
        "/admin/users",
    ) == (
        ShowModel,
        {
            "model": "users",
        },
    )

    # get_component: index
    assert get_component(
        routes,
        "/",
    ) == (
        PageIndex,
        {},
    )

    # get_component: invalid pattern (str instead of int)
    assert get_component(
        routes,
        "/admin/users/foo/"
    ) == (
        None,
        None,
    )

    # get_component: no matching route
    assert get_component(
        routes,
        "/foo"
    ) == (
        None,
        None,
    )

    # get_url: with route_args
    assert get_url(
        routes,
        "show_model_object",
        {
            "model": "users",
            "pk": 10,
        },
    ) == "/admin/users/10/"

    # get_url: without route_args
    assert get_url(
        routes,
        "admin_index",
    ) == "/admin/"

    # get_url: failing checks
    with pytest.raises(InvalidRouteArgsError):
        assert get_url(
            routes,
            "show_model_object",
            {
                "model": "users",
                "pk": "foo",
            },
        )

    assert get_url(
        routes,
        "show_model_object",
        {
            "model": "users",
            "pk": "foo",
        },
        checks=False
    ) == "/admin/users/foo/"

    # get_url: unknown url
    with pytest.raises(UnknownRouteError):
        assert get_url(routes, "foo")

    # get_url: missing argument
    with pytest.raises(InvalidRouteArgsError):
        assert get_url(
            routes,
            "show_model_object",
            {
                "model": "users",
            },
        )

    # get_url: queries
    assert get_url(
        routes,
        "admin_index",
        query={
            "foo": "bar",
            "bar": ["foo1", "foo2"],
        }
    ) == "/admin/?foo=bar&bar=foo1&bar=foo2"

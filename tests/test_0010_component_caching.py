import pytest


def test_component_caching():
    from falk.component_caching import (
        get_component_id,
        cache_component,
        get_component,
    )

    from falk.errors import UnknownComponentIdError, InvalidComponentError
    from falk.components import HTML5Base, ItWorks
    from falk.app import get_default_app

    app = get_default_app()

    # at the start, the cache should be empty
    assert not app["component_cache"]

    # different components should generate different component ids
    component_id_1 = get_component_id(HTML5Base, app)
    component_id_1_2 = get_component_id(HTML5Base, app)
    component_id_2 = get_component_id(ItWorks, app)

    assert component_id_1 == component_id_1_2
    assert component_id_1 != component_id_2

    # test caching
    component_id_1 = cache_component(HTML5Base, app)
    component_id_2 = cache_component(ItWorks, app)

    assert HTML5Base in app["component_cache"]
    assert component_id_1 in app["component_cache"]
    assert app["component_cache"][component_id_1] == HTML5Base
    assert get_component(component_id_1, app) == HTML5Base

    assert ItWorks in app["component_cache"]
    assert component_id_2 in app["component_cache"]
    assert app["component_cache"][component_id_2] == ItWorks
    assert get_component(component_id_2, app) == ItWorks

    # caching should be skipped if the component is already cached
    cache_component(HTML5Base, app)

    assert len(app["component_cache"].keys()) == 4

    # errors
    # all components need to be callable
    with pytest.raises(InvalidComponentError):
        cache_component("foo", app)

    # unknown component ids
    with pytest.raises(UnknownComponentIdError):
        get_component("foo", app)


def test_component_id_collisions():
    from falk.component_caching import get_component_id
    from falk.app import get_default_app

    app = get_default_app()

    def get_component_1():
        def foo():
            return ""

        return foo

    def get_component_2():
        def foo():
            return ""

        return foo

    component_1_id = get_component_id(get_component_1(), app)
    component_2_id = get_component_id(get_component_2(), app)

    assert component_1_id != component_2_id

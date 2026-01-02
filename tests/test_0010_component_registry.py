def test_component_registry():
    from falk.component_registry import get_component_id, register_component
    from falk.apps import get_default_app

    def Component1(context):
        pass

    def Component2(context):
        pass

    def Component3(context, Component1=Component1, Component2=Component2):
        pass

    mutable_app = get_default_app()

    # the component registry should be empty at start
    assert len(mutable_app["components"]) == 0

    # component ids need to be unique but reproducible
    get_component_id(
        Component1,
        mutable_app,
    ) == get_component_id(
        Component1,
        mutable_app,
    )

    get_component_id(
        Component2,
        mutable_app,
    ) == get_component_id(
        Component2,
        mutable_app,
    )

    get_component_id(
        Component3,
        mutable_app,
    ) == get_component_id(
        Component3,
        mutable_app,
    )

    component_id_1 = get_component_id(Component1, mutable_app)
    component_id_2 = get_component_id(Component2, mutable_app)
    component_id_3 = get_component_id(Component3, mutable_app)

    assert len(set([component_id_1, component_id_2, component_id_3])) == 3

    # components without dependencies
    mutable_app["components"].clear()
    register_component(Component1, mutable_app)

    assert len(mutable_app["components"].keys()) == 2
    assert Component1 in mutable_app["components"].values()
    assert Component2 not in mutable_app["components"].values()
    assert Component3 not in mutable_app["components"].values()

    mutable_app["components"].clear()
    register_component(Component2, mutable_app)

    assert len(mutable_app["components"].keys()) == 2
    assert Component1 not in mutable_app["components"].values()
    assert Component2 in mutable_app["components"].values()
    assert Component3 not in mutable_app["components"].values()

    # components with dependencies
    mutable_app["components"].clear()
    register_component(Component3, mutable_app)

    assert len(mutable_app["components"].keys()) == 6
    assert Component1 in mutable_app["components"].values()
    assert Component2 in mutable_app["components"].values()
    assert Component3 in mutable_app["components"].values()


def test_component_id_collisions():
    from falk.component_registry import get_component_id
    from falk.apps import get_default_app

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


def test_file_upload_handler_dependencies():
    from falk.component_registry import (
        get_file_upload_handler,
        register_component,
        get_component_id,
    )

    from falk.apps import get_default_app

    mutable_app = get_default_app()

    def handle_file_upload():
        pass

    def Component1(handle_file_upload=handle_file_upload):
        pass

    def Component2():
        pass

    register_component(
        component=Component1,
        mutable_app=mutable_app,
    )

    register_component(
        component=Component2,
        mutable_app=mutable_app,
    )

    assert get_file_upload_handler(
        component_id=get_component_id(
            component=Component1,
            mutable_app=mutable_app,
        ),
        mutable_app=mutable_app,
    ) is handle_file_upload

    assert get_file_upload_handler(
        component_id=get_component_id(
            component=Component2,
            mutable_app=mutable_app,
        ),
        mutable_app=mutable_app,
    ) is mutable_app["settings"]["default_file_upload_handler"]

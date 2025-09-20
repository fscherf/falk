import pytest


def test_add_attributes():
    from falk.errors import MissingRootNodeError
    from falk.html import add_attributes_to_root_node

    attributes = {
        "data-falk-id": "id",
        "data-falk-token": "token",
    }

    # no start tag
    with pytest.raises(MissingRootNodeError):
        add_attributes_to_root_node("foo", attributes)

    with pytest.raises(MissingRootNodeError):
        add_attributes_to_root_node("foo</div>", attributes)

    # simple HTML tag
    updated_html = add_attributes_to_root_node(
        '<div id="foo">bar</div>',
        attributes,
    )

    assert updated_html == '<div id="foo" data-falk-id="id" data-falk-token="token">bar</div>'  # NOQA

    # nested HTML tag
    updated_html = add_attributes_to_root_node(
        '<div id="foo"><div>bar<br/></div></div>',
        attributes,
    )

    assert updated_html == '<div id="foo" data-falk-id="id" data-falk-token="token"><div>bar<br/></div></div>'  # NOQA

    # self closing HTML tag
    updated_html = add_attributes_to_root_node(
        '<br id="foo" />',
        attributes,
    )

    assert updated_html == '<br id="foo" data-falk-id="id" data-falk-token="token" />'  # NOQA

    # key only HTML attributes
    updated_html = add_attributes_to_root_node(
        '<div foo></div>',
        attributes,
    )

    assert updated_html == '<div foo data-falk-id="id" data-falk-token="token"></div>'  # NOQA

    # whitespace
    updated_html = add_attributes_to_root_node(
        '\n \n<div id="foo">\nbar</div>',
        attributes,
    )

    assert updated_html == '\n \n<div id="foo" data-falk-id="id" data-falk-token="token">\nbar</div>'  # NOQA


def test_parse_component_template():
    from falk.html import parse_component_template

    from falk.html import (
        InvalidScriptBlockError,
        InvalidStyleBlockError,
        MultipleRootNodesError,
        MissingRootNodeError,
        UnbalancedTagsError,
        UnclosedTagsError,
    )

    # simple HTML block
    template = """
        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []
    assert blocks["styles"] == []

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == []

    # simple style block
    template = """
        <style>
            .foo { color: red }
        </style>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []
    assert blocks["styles"] == [".foo { color: red }"]

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == []

    # style block with multiple style tags
    template = """
        <style>
            .foo { color: red }
        </style>
        <style>
            .bar { color: red }
            .baz { color: red }
        </style>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []

    assert blocks["styles"][0] == ".foo { color: red }"
    assert ".bar { color: red }" in blocks["styles"][1]
    assert ".baz { color: red }" in blocks["styles"][1]

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == []

    # style URLS
    template = """
        <link href="foo.css">

        <style>
            .foo { color: red }
        </style>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == ["foo.css"]
    assert blocks["styles"] == [".foo { color: red }"]

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == []

    # styles with additional attributes
    template = """
        <style foo="bar">
            .foo { color: red }
        </style>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []
    assert blocks["styles"] == [".foo { color: red }"]

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == []

    # simple script block
    template = """
        <script>
            $.post("/test");
        </script>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []
    assert blocks["styles"] == []

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == ['$.post("/test");']

    # script block with multiple script tags
    template = """
        <script>
            $.post("/test1");
        </script>
        <script>
            $.post("/test2");
            $.get("/test2");
        </script>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []
    assert blocks["styles"] == []

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []

    assert blocks["scripts"][0] == '$.post("/test1");'
    assert '$.post("/test2");' in blocks["scripts"][1]
    assert '$.get("/test2");' in blocks["scripts"][1]

    # scripts with additional attributes
    template = """
        <script foo="bar">
            $.post("/test");
        </script>

        <div id="foo">Foo</div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == []
    assert blocks["styles"] == []

    assert blocks["html"] == '<div id="foo">Foo</div>'

    assert blocks["script_urls"] == []
    assert blocks["scripts"] == ['$.post("/test");']

    # complex cases
    # everything at once
    template = """
        <link href="foo.css" />
        <style>
            .foo { color: red }
        </style>

        <!DOCTYPE HTML><div id="foo">foo<br /></div>

        <script src="foo.js"></script>
        <script>
            $.post("/test");
        </script>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == ["foo.css"]
    assert blocks["styles"] == [".foo { color: red }"]

    assert blocks["html"] == '<!DOCTYPE HTML>\n<div id="foo">foo<br /></div>'

    assert blocks["script_urls"] == ["foo.js"]
    assert blocks["scripts"] == ['$.post("/test");']

    # everything at once, different order
    template = """
        <script src="foo.js"></script>
        <script>
            $.post("/test");
        </script>

        <style>
            .foo { color: red }
        </style>

        <link href="foo.css" />

        <!DOCTYPE HTML><div id="foo">foo<br /></div>
    """

    blocks = parse_component_template(template)

    assert blocks["style_urls"] == ["foo.css"]
    assert blocks["styles"] == [".foo { color: red }"]

    assert blocks["html"] == '<!DOCTYPE HTML>\n<div id="foo">foo<br /></div>'

    assert blocks["script_urls"] == ["foo.js"]
    assert blocks["scripts"] == ['$.post("/test");']

    # errors
    # MissingRootNodeError
    with pytest.raises(MissingRootNodeError):
        parse_component_template("""
            <script>console.log('foo');</script>
        """)

    with pytest.raises(MissingRootNodeError):
        parse_component_template("""
            foo
        """)

    with pytest.raises(MissingRootNodeError):
        parse_component_template("""
        """)

    # MultipleRootNodesError
    with pytest.raises(MultipleRootNodesError):
        parse_component_template("""
            <div id="foo"></div>
            <div id="bar"></div>
        """)

    with pytest.raises(MultipleRootNodesError):
        parse_component_template("""
            <br />
            <div id="bar"></div>
        """)

    with pytest.raises(MultipleRootNodesError):
        parse_component_template("""
            <br />
            <br />
        """)

    with pytest.raises(MultipleRootNodesError):
        parse_component_template("""
            foo
            <br />
        """)

    # InvalidScriptBlockError
    with pytest.raises(InvalidScriptBlockError):
        parse_component_template("""
            <script src="foo.js">
                $.post("/test");
            </script>
        """)

    # UnbalancedTagsError
    with pytest.raises(UnbalancedTagsError):
        parse_component_template("""
            <div>
                <span>foo</div>
            </div>
        """)

    with pytest.raises(UnbalancedTagsError):
        parse_component_template("""
            </div>
        """)

    # UnclosedTagsError
    with pytest.raises(UnclosedTagsError):
        parse_component_template("""
            <span>foo
        """)


def test_get_node_id():
    from falk.errors import InvalidSettingsError
    from falk.apps import get_default_app
    from falk.html import get_node_id

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

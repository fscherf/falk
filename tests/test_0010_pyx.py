def test_pyx_to_jinja2_transpiling():
    """
    This test tests the transpiling from PYX to Jinja2 templates implementing
    a simple render function and checking PYX snippets against rendered HTML.

    This only ensures that the transpiler produces Jinja2 source that is in
    theory renderable. It does not use the rendering system.
    """

    from jinja2 import Template, pass_context

    from falk.pyx import transpile_pyx_to_jinja2

    @pass_context
    def _render_component(context, component_name, caller=None, **props):
        component = context[component_name]

        return component(**props)

    def _component(class_name, **props):
        attribute_string_parts = []

        for key, value in sorted(props.items()):
            attribute_string_parts.append(
                f'{key}="{value}"',
            )

        attribute_string = " ".join(attribute_string_parts)

        if attribute_string:
            attribute_string = " " + attribute_string

        return f'<div class="{class_name}"{attribute_string}></div>'

    def Component1(**props):
        return _component("c1", **props)

    def Component2(**props):
        return _component("c2", **props)

    def _render(pyx_source):
        jinja2_source = transpile_pyx_to_jinja2(pyx_source)
        template = Template(jinja2_source)

        return template.render({
            "_render_component": _render_component,
            "Component1": Component1,
            "Component2": Component2,
        })

    # HTML
    assert _render(
        '<div foo="bar" bar="baz" baz><br /></div>'
    ) == (
        '<div foo="bar" bar="baz" baz><br /></div>'
    )

    assert _render(
        '<div foo="bar"><span bar="baz"></span></div>'
    ) == (
        '<div foo="bar"><span bar="baz"></span></div>'
    )

    # HTML with declaration
    assert _render(
        '<!DOCTYPE HTML>\n<div foo="bar" bar="baz" baz><br /></div>'
    ) == (
        '<!DOCTYPE HTML>\n<div foo="bar" bar="baz" baz><br /></div>'
    )

    # PYX components
    assert _render(
        '<Component1></Component1>'
    ) == (
        '<div class="c1"></div>'
    )

    assert _render(
        '<Component2></Component2>'
    ) == '<div class="c2"></div>'

    assert _render(
        '<Component1 a=1></Component1>'
    ) == (
        '<div class="c1" a="1"></div>'
    )

    assert _render(
        '<Component1 a />'
    ) == (
        '<div class="c1" a="None"></div>'
    )

    assert _render(
        '{% for i in range(2) %}<Component1 a="{{ i }}" />{% endfor %}'
    ) == (
        '<div class="c1" a="0"></div><div class="c1" a="1"></div>'
    )

    # mixed HTML and PYX
    assert _render(
        '<div a="a" b><Component2 c="c" d="{{ 1 + 1 }}" /></div>'
    ) == (
        '<div a="a" b><div class="c2" c="c" d="2"></div></div>'
    )

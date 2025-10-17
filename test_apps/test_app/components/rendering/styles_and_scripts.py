from test_app.components.events.click import Counter
from test_app.components.base import Base


def Component(context, Counter=Counter):
    context.update({
        "Counter": Counter,
    })

    return """
        <link href="/static/component.css">

        <style>
            #component-inline-style::before {
                content: "Loading inline styles works";
            }
        </style>

        <div class="component">
            <h3>Component</h3>

            <div id="component-external-style"></div>
            <div id="component-inline-style"></div>

            <div
              id="component-external-script"
              onrender="ComponentExternalFunction(this);"></div>

            <div
              id="component-inline-script"
              onrender="ComponentInlineFunction(this);"></div>

            <h3>Counter</h3>
            <p>
                The counter is here to ensure that Falk still works after we
                loaded and executed external and inline scripts.
            </p>

            <Counter />
        </div>

        <script src="/static/component.js"></script>

        <script>
            function ComponentInlineFunction(element) {
                element.innerHTML = "Loading inline scripts works";
            }
        </script>
    """


def StylesAndScripts(
        context,
        Base=Base,
        Component=Component,
):

    context.update({
        "Base": Base,
        "Component": Component,
    })

    return """
        <Base title="Styles and Scripts">
            <h2>Styles and Scripts</h2>
            <Component />
        </Base>
    """


def CodeSplitting(
        context,
        state,
        initial_render,
        add_static_dir,
        Base=Base,
        Component=Component,
):

    if initial_render:
        state["load_component"] = False

    def load_component():
        state["load_component"] = True

    context.update({
        "Base": Base,
        "Component": Component,
        "load_component": load_component,
    })

    return """
        <Base title="Code Splitting">
            <h2>Code Splitting</h2>

            {% if state.load_component %}
                <Component />
            {% else %}
                <button
                  onclick="{{ callback(load_component) }}"
                  id="load-component">
                    Load Component
                </button>
            {% endif %}
        </Base>
    """

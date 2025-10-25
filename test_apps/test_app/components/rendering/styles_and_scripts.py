from test_app.components.events.click import Counter
from test_app.components.base import Base


def Component(
        Counter=Counter,
        static_dirs=[
            "./static/",
        ],
):
    return """
        <link href="/static/app-component.css">
        <link href="/static/package-component.css">

        <style>
            #component-inline-style::before {
                content: "Loading inline styles works";
            }
        </style>

        <div class="component" onrender="
            ((element) => {
                ComponentAppExternalFunction(element);
                ComponentPackageExternalFunction(element);
                ComponentInlineFunction(element);
            })(this);
        ">

            <h3>Component</h3>

            <div id="component-app-external-style"></div>
            <div id="component-package-external-style"></div>
            <div id="component-inline-style"></div>

            <div id="component-app-external-script"></div>
            <div id="component-package-external-script"></div>
            <div id="component-inline-script"></div>

            <h3>Counter</h3>
            <p>
                The counter is here to ensure that Falk still works after we
                loaded and executed external and inline scripts.
            </p>

            <Counter />
        </div>

        <script src="/static/app-component.js"></script>
        <script src="/static/package-component.js"></script>

        <script>
            function ComponentInlineFunction(element) {
                element.querySelector(
                    "#component-inline-script",
                ).innerHTML = "Loading inline scripts works";
            }
        </script>
    """


def StylesAndScripts(Base=Base, Component=Component):
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
        Base=Base,
        Component=Component,
):

    if initial_render:
        state["load_component"] = False

    def load_component():
        state["load_component"] = True

    context.update({
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

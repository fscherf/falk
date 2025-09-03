import os

from jinja2 import Template, pass_context

from falk.html import add_attributes_to_root_node, parse_component_template
from falk.dependency_injection import run_callback
from falk.errors import InvalidComponentError
from falk.pyx import transpile_pyx_to_jinja2

CLIENT_JS_PATH = os.path.join(
    os.path.dirname(__file__),
    "client/falk.js",
)


@pass_context
def _render_component(context, component, caller=None, **props):
    if "children" not in props:
        props["children"] = ""

    if caller:
        props["children"] = caller()

    return render_component(
        component=component,
        app=context["app"],
        request=context["request"],
        response=context["response"],
        component_props=props,
        dependency_cache=context["_dependency_cache"],
    )


@pass_context
def _callback(context, callback_or_callback_name, delay=None, initial=False):
    callback_name = ""

    if initial and context["initial_render"]:
        return ""

    if isinstance(callback_or_callback_name, str):
        callback_name = callback_or_callback_name

    elif callable(callback_or_callback_name):
        for key, value in context.items():
            if value is callback_or_callback_name:
                callback_name = key

                break

    # provoke a KeyError if the callback does not exist
    context[callback_name]

    callback_args = [
        context["node_id"],
        callback_name,
    ]

    if delay is not None:
        callback_args.append(delay)

    callback_args_string = ", ".join([repr(i) for i in callback_args])

    return f"falk.runCallback({callback_args_string});"


@pass_context
def _falk_scripts(context):
    with open(CLIENT_JS_PATH, "r") as f:
        return f'<script>{f.read()}</script>'


def render_component(
        component,
        app,
        request,
        response,
        node_id=None,
        component_state=None,
        component_props=None,
        dependency_cache=None,
        run_component_callback="",
):

    # check component
    if not callable(component):
        raise InvalidComponentError(
            "components have to be callable",
        )

    # setup state
    initial_render = False

    if not node_id:
        node_id = app["settings"]["get_node_id"](app["settings"])

    if not component_state:
        component_state = {}
        initial_render = True

    if not component_props:
        component_props = {}

    # setup dependency cache
    if dependency_cache is None:
        dependency_cache = {}

    # setup template context
    template_context = {

        # internal API
        "_dependency_cache": dependency_cache,
        "_render_component": _render_component,

        # public API
        "app": app,
        "settings": app["settings"],
        "request": request,
        "response": response,
        "node_id": node_id,
        "state": component_state,
        "props": component_props,

        "callback": _callback,
        "falk_scripts": _falk_scripts,
    }

    # run component with dependencies
    dependencies = {

        # external dependencies
        "app": app,
        "settings": app["settings"],
        "request": request,
        "response": response,
        "initial_render": initial_render,
        "props": component_props,

        # state
        "node_id": node_id,
        "context": template_context,
        "state": component_state,
    }

    pyx_source = run_callback(
        callback=component,
        dependencies=dependencies,
        providers=app["settings"]["providers"],
        cache=dependency_cache,
    )

    if run_component_callback:
        run_callback(
            callback=template_context[run_component_callback],
            dependencies=dependencies,
            providers=app["settings"]["providers"],
            cache=dependency_cache,
        )

    # transpile pyx to jinja2
    jinja2_source = transpile_pyx_to_jinja2(
        pyx_source=pyx_source,
    )

    # render jinja2 template
    template = Template(jinja2_source)

    component_template = template.render(template_context)

    # create token
    component_id = app["settings"]["cache_component"](
        component=component,
        app=app,
    )

    token = app["settings"]["encode_token"](
        component_id=component_id,
        component_state=component_state,
        settings=app["settings"],
    )

    # post process HTML
    component_blocks = parse_component_template(
        component_template=component_template,
    )

    html = add_attributes_to_root_node(
        html_source=component_blocks["html"],
        attributes={
            "data-falk-id": node_id,
            "data-falk-token": token,
        },
    )

    # finish
    return html

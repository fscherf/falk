from urllib.parse import quote
import builtins
import json
import os

from jinja2 import Template, pass_context

from falk.dependency_injection import run_callback, get_dependencies
from falk.errors import InvalidComponentError, UnknownComponentError
from falk.component_templates import parse_component_template
from falk.utils.iterables import extend_with_unique_values
from falk.immutable_proxy import get_immutable_proxy


@pass_context
def _render_component(
        context,
        caller=None,
        _component_name="",
        _node_id=None,
        _token=None,
        **props,
):

    # find component in context
    if _component_name not in context["_components"]:

        # TODO: state which component is lacking the dependency
        raise UnknownComponentError(
            f'component "{_component_name}" was not found in the dependencies',
        )

    component = context["_components"][_component_name]

    # prepare props
    if "props" in props:
        # We got the props of our caller passed in
        # (`<Component props="{{ props }}" ... />`), so we use the passed
        # props as base and our own props as overrides.

        props = {
            **props["props"],
            **props,
        }

    if "children" not in props:
        props["children"] = ""

    if caller:
        props["children"] = caller()

    parts = render_component(
        component=component,
        mutable_app=context["mutable_app"],
        request=context["mutable_request"],
        response=context["response"],
        component_props=props,
        node_id=_node_id,
        token=_token,
        is_root=False,
        parts=context["_parts"],
    )

    return parts["html"]


@pass_context
def _callback(
        context,
        callback_or_callback_name,
        callback_args=None,
        stop_event=True,
        delay=None,
):

    callback_name = ""

    if isinstance(callback_or_callback_name, str):
        callback_name = callback_or_callback_name

    elif callable(callback_or_callback_name):
        for key, value in context.items():
            if value is callback_or_callback_name:
                callback_name = key

                break

    # provoke a KeyError if the callback does not exist
    context[callback_name]

    options = {
        "nodeId": context["node_id"],
        "callbackName": callback_name,
        "callbackArgs": callback_args,
        "stopEvent": stop_event,
        "delay": delay,
    }

    options_string = quote(json.dumps(options))

    return f"falk.runCallback({{event: event, optionsString: '{options_string}'}});"


@pass_context
def _falk_styles(context):
    return render_styles(
        app=context["app"],
        styles=context["_parts"]["styles"],
    )


@pass_context
def _falk_scripts(context):
    return render_scripts(
        app=context["app"],
        scripts=context["_parts"]["scripts"],
    )


def render_styles(app, styles):
    return "\n".join(styles)


def render_scripts(app, scripts):
    client_url = os.path.join(
        app["settings"]["static_url_prefix"],
        "falk/falk.js",
    )

    return "\n".join([
        f'<script src="{client_url}"></script>',
        *scripts,
    ])


def render_body(app, parts):
    return (
        render_styles(
            app=app,
            styles=parts["styles"],
        ) +
        parts["html"] +
        render_scripts(
            app=app,
            scripts=parts["scripts"],
        )
    )


def render_component(
        component,
        mutable_app,
        request,
        response,
        node_id=None,
        token=None,
        component_state=None,
        component_props=None,
        is_root=True,
        run_component_callback="",
        parts=None,
):

    # TODO: add dependency caching once `uncachable_dependencies`
    # is implemented.

    # TODO: Since mutation requests return HTML now, it would be much nicer if
    # this method would return an HTML document as a string.

    if parts is None:
        parts = {
            "html": "",
            "styles": [],
            "scripts": [],
            "callbacks": [],
            "flags": {
                "force_rendering": False,
                "skip_rendering": False,
            },
        }

    # check component
    if not callable(component):
        raise InvalidComponentError(
            "components have to be callable",
        )

    # setup component state
    initial_render = False

    if not node_id:
        node_id = mutable_app["settings"]["get_node_id"](
            mutable_app=mutable_app,
        )

    if component_state is None:
        component_state = {}
        initial_render = True

    if component_props is None:
        component_props = {}

    # setup dependencies and template context
    data = {
        # meta data
        "caller": component,
        "initial_render": initial_render,
        "is_root": is_root,

        # immutable
        "app": get_immutable_proxy(
            data=mutable_app,
            name="app",
            mutable_version_name="mutable_app",
        ),

        "settings": get_immutable_proxy(
            data=mutable_app["settings"],
            name="settings",
            mutable_version_name="mutable_settings",
        ),

        "request": get_immutable_proxy(
            data=request,
            name="request",
            mutable_version_name="mutable_request",
        ),

        "props": get_immutable_proxy(
            data=component_props,
            name="props",
            mutable_version_name="mutable_props",
        ),

        # explicitly mutable
        "mutable_app": mutable_app,
        "mutable_settings": mutable_app["settings"],
        "mutable_request": request,
        "mutable_props": component_props,

        # mutable by design
        # (some of them are implicitly immutable due to Python internals)
        "node_id": node_id,
        "state": component_state,
        "response": response,
    }

    template_context = {
        **builtins.__dict__,
        **data,

        # TODO: we inspect the component at least twice here. Explicitly using
        # `get_dependencies()` and inexplicitly using `run_callback()`.
        "_components": get_dependencies(component)[1],

        "_render_component": _render_component,
        "_parts": parts,
        "callback": _callback,
        "falk_styles": _falk_styles,
        "falk_scripts": _falk_scripts,

        # This is a simple NOP to make calls like
        # `{{ callback(render) }}` for simply re rendering work.
        "render": lambda: None,

        **mutable_app["settings"]["extra_template_context"],
    }

    dependencies = {
        **data,
        "context": template_context,
    }

    # run component
    component_template = run_callback(
        callback=component,
        dependencies=dependencies,
        providers=mutable_app["settings"]["providers"],
        run_coroutine_sync=mutable_app["settings"]["run_coroutine_sync"],
    )

    # Check if the component finished the response. If so, we can skip all
    # parsing and post processing.
    # This happens when files, binary data, or JSON is returned.
    if response["is_finished"]:
        return parts

    # `run_component_callback` is set to string that points to a callback
    # in the template context of the component when we receive a
    # mutation request.
    # The callback needs to run before we render the jinja2 template because
    # it will most likely mutate the template context.
    if run_component_callback:
        dependencies.update({
            "args": request["callback_args"],
            "event": request["event"],
        })

        run_callback(
            callback=template_context[run_component_callback],
            dependencies=dependencies,
            providers=mutable_app["settings"]["providers"],
            run_coroutine_sync=mutable_app["settings"]["run_coroutine_sync"],
        )

    # parse component template
    def _hash_string(string):
        return mutable_app["settings"]["hash_string"](
            mutable_app=mutable_app,
            string=string,
        )

    component_blocks = parse_component_template(
        component_template=component_template,
        component=component,
        static_url_prefix=mutable_app["settings"]["static_url_prefix"],
        hash_string=_hash_string,
    )

    # add styles and scripts to the output
    # We use `extend_with_unique_values` here to prevent styles and scripts
    # to be added to the document more than once if a component is used
    # multiple times or if two components share a static file.
    extend_with_unique_values(
        parts["styles"],
        component_blocks["styles"],
    )

    extend_with_unique_values(
        parts["scripts"],
        component_blocks["scripts"],
    )

    # generate token
    if not token:
        component_id = mutable_app["settings"]["get_component_id"](
            component=component,
            mutable_app=mutable_app,
        )

        token = mutable_app["settings"]["encode_token"](
            component_id=component_id,
            component_state=component_state,
            mutable_app=mutable_app,
        )

    template_context["_token"] = token

    # render jinja2 template
    template = Template(component_blocks["jinja2_template"])

    parts["html"] = template.render(template_context)

    # finish
    return parts

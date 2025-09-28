import os

from jinja2 import Template, pass_context

from falk.errors import InvalidComponentError, UnknownComponentError
from falk.component_templates import parse_component_template
from falk.utils.iterables import extend_with_unique_values
from falk.immutable_proxy import get_immutable_proxy
from falk.dependency_injection import run_callback


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
    if _component_name not in context:
        raise UnknownComponentError(
            f'component "{_component_name}" was not found in the context',
        )

    component = context[_component_name]

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
def _falk_styles(context):
    return Template("""
        {% for url in style_urls %}
            <link rel="stylesheet" href="{{ url }}">
        {% endfor %}
    """).render({
        "settings": context["settings"],
        "style_urls": context["_parts"]["style_urls"],
    })


@pass_context
def _falk_scripts(context):
    return Template("""
        <script src="{{ settings['static_url_prefix'] }}falk/falk.js"></script>

        {% for url in script_urls %}
            <script src="{{ url }}"></script>
        {% endfor %}
    """).render({
        "settings": context["settings"],
        "script_urls": context["_parts"]["script_urls"],
    })


def _resolve_urls(component, urls, static_url_prefix):
    resolved_urls = set()

    for url in urls:

        # external URLs
        if "://" in url:
            resolved_urls.add(url)

        # static URLs
        prefix = "/static/"

        if url.startswith(prefix):
            resolved_urls.add(
                os.path.join(
                    static_url_prefix,
                    url[len(prefix):],
                ),
            )

        else:
            raise NotImplementedError(
                "only external and static URLs are supported",
            )

    return urls


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

    # TODO: When rendering components that include another component as their
    # root node, we generate to many tokens.

    if parts is None:
        parts = {
            "html": "",
            "style_urls": [],
            "script_urls": [],
            "tokens": {},
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

    if not component_state:
        component_state = {}
        initial_render = True

    if not component_props:
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
        **data,
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
        return ""

    # `run_component_callback` is set to string that points to a callback
    # in the template context of the component when we receive a
    # mutation request.
    # The callback needs to run before we render the jinja2 template because
    # it will most likely mutate the template context.
    if run_component_callback:
        run_callback(
            callback=template_context[run_component_callback],
            dependencies=dependencies,
            providers=mutable_app["settings"]["providers"],
            run_coroutine_sync=mutable_app["settings"]["run_coroutine_sync"],
        )

    # parse component template
    component_blocks = parse_component_template(
        component_template=component_template,
    )

    # style URLs
    extend_with_unique_values(
        parts["style_urls"],
        _resolve_urls(
            component=component,
            urls=component_blocks["style_urls"],
            static_url_prefix=mutable_app["settings"]["static_url_prefix"],
        ),
    )

    # script URLs
    extend_with_unique_values(
        parts["script_urls"],
        _resolve_urls(
            component=component,
            urls=component_blocks["script_urls"],
            static_url_prefix=mutable_app["settings"]["static_url_prefix"],
        ),
    )

    # generate token
    component_id = mutable_app["settings"]["cache_component"](
        component=component,
        mutable_app=mutable_app,
    )

    token = mutable_app["settings"]["encode_token"](
        component_id=component_id,
        component_state=component_state,
        mutable_app=mutable_app,
    )

    template_context["_token"] = token
    parts["tokens"][node_id] = token

    # render jinja2 template
    template = Template(component_blocks["jinja2_template"])

    parts["html"] = template.render(template_context)

    # finish
    return parts

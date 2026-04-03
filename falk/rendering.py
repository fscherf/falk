from urllib.parse import quote
import builtins
import json

from jinja2 import Template, pass_context

from falk.dependency_injection import run_callback, get_dependencies
from falk.component_templates import parse_component_template
from falk.utils.iterables import extend_with_unique_values
from falk.immutable_proxy import get_immutable_proxy
from falk.import_strings import get_import_string
from falk.static_files import get_static_url
from falk.routing import get_url

from falk.errors import (
    ComponentExecutionError,
    ComponentTemplatingError,
    InvalidComponentError,
    UnknownComponentError,
    BadRequestError,
    FalkError,
)

FALK_CLIENT_SCRIPT = """
<script src="{{ falk.get_static_url('falk/falk.js') }}"></script>
"""

FALK_INIT_SCRIPT = """
<script fx-id="falk/init">
    falk.settings = JSON.parse('{{ settings_string }}');
    falk.tokens = JSON.parse(`{{ token_string }}`);
    falk.initialCallbacks = JSON.parse(`{{ callback_string }}`);

    falk.init();
</script>
"""


@pass_context
def _render_component(
        template_context,
        caller=None,
        _component_name="",
        _node_id=None,
        _token=None,
        **props,
):

    # find component in template_context
    if _component_name not in template_context["falk"]["_components"]:
        caller_import_string = get_import_string(template_context["caller"])

        raise UnknownComponentError(
            f'{caller_import_string}: component "{_component_name}" was not found in the dependencies',  # NOQA
        )

    component = template_context["falk"]["_components"][_component_name]

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
        mutable_app=template_context["mutable_app"],
        request=template_context["mutable_request"],
        response=template_context["response"],
        component_props=props,
        node_id=_node_id,
        token=_token,
        is_root=False,
        parts=template_context["falk"]["_parts"],
    )

    return parts["html"]


@pass_context
def _run_callback(
        template_context,
        callback_name,
        callback_args=None,
        selector="self",
        stop_event=True,
        delay=None,
):

    # TODO: add tests for selector option

    def _raise_invalid_component_error(message):
        caller_import_string = get_import_string(
            template_context["caller"],
        )

        raise InvalidComponentError(
            f"{caller_import_string}: {message}",
        )

    # callback_name
    if not isinstance(callback_name, str):
        _raise_invalid_component_error("callback names need to be a strings")

    # callback_args
    if callback_args and not isinstance(callback_args, (dict, list)):
        _raise_invalid_component_error(
            "'callback_args' needs to be either dict or list",
        )

    # If the selector is not "self", we can't check whether a callback name is
    # valid nor the selected component is stateful.
    if selector == "self":

        # check if callback exist
        if callback_name not in template_context["falk"]["_callbacks"]:
            _raise_invalid_component_error(
                f"unknown callback '{callback_name}'",
            )

        # check if component is stateful
        if not template_context["falk"]["_parts"]["flags"]["state"]:
            _raise_invalid_component_error(
                "callbacks can not be used if component state is disabled",
            )

    # generate selector
    if selector == "self":
        node_id = template_context["node_id"]
        selector = f"[fx-id={node_id}]"

    # generate options string
    options = {
        "selector": selector,
        "callbackName": callback_name,
        "callbackArgs": callback_args,
        "stopEvent": stop_event,
        "delay": delay,
    }

    options_string = quote(json.dumps(options))

    return f"falk.runCallback({{event: event, optionsString: '{options_string}'}});"  # NOQA


@pass_context
def _get_url(
    template_context,
    route_name,
    route_args=None,
    query=None,
    checks=True,
):

    return get_url(
        routes=template_context["app"]["routes"],
        route_name=route_name,
        route_args=route_args,
        query=query,
        prefix=template_context["request"]["root_path"],
        checks=checks,
    )


@pass_context
def _get_static_url(
    template_context,
    rel_path,
):

    settings = template_context["mutable_app"]["settings"]

    return get_static_url(
        root_path=template_context["request"]["root_path"] or "/",
        static_url_prefix=settings["static_url_prefix"],
        rel_path=rel_path,
    )


@pass_context
def _get_upload_token(template_context, plain=False):
    mutable_app = template_context["mutable_app"]

    component_id = mutable_app["settings"]["get_component_id"](
        component=template_context["caller"],
        mutable_app=template_context["mutable_app"],
    )

    if plain:
        return component_id

    return f'<input type="hidden" name="falk/upload-token" value="{component_id}">'  # NOQA


@pass_context
def _get_styles(template_context):
    return _render_styles(
        mutable_app=template_context["mutable_app"],
        mutable_request=template_context["mutable_request"],
        parts=template_context["falk"]["_parts"],
    )


@pass_context
def _get_scripts(template_context):
    return _render_scripts(
        mutable_app=template_context["mutable_app"],
        mutable_request=template_context["mutable_request"],
        parts=template_context["falk"]["_parts"],
    )


def get_template_context(
        mutable_app,
        mutable_request,
        extra_template_context=None,
        parts=None,
        components=None,
        callbacks=None,
):

    if extra_template_context is None:
        extra_template_context = {}

    if parts is None:
        parts = {}

    if components is None:
        components = {}

    if callbacks is None:
        callbacks = {

            # This is a simple NOP to make calls like
            # `{{ falk.run_callback('render') }}` for simply re rendering work.
            "render": lambda: None,
        }

    return {
        **builtins.__dict__,

        # public immutable data
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
            data=mutable_request,
            name="request",
            mutable_version_name="mutable_request",
        ),

        # public mutable data
        "mutable_app": mutable_app,
        "mutable_settings": mutable_app["settings"],
        "mutable_request": mutable_request,

        **extra_template_context,
        **mutable_app["settings"]["extra_template_context"],

        # The `falk` namespace is always added last so it can not be
        # overloaded accidentally.
        "falk": {

            # internal data
            "_components": components,
            "_callbacks": callbacks,
            "_parts": parts,

            # internal API
            "_render_component": _render_component,

            # public API
            "get_url": _get_url,
            "get_static_url": _get_static_url,
            "get_styles": _get_styles,
            "get_scripts": _get_scripts,
            "get_upload_token": _get_upload_token,
            "run_callback": _run_callback,
        },
    }


def _render_styles(mutable_app, mutable_request, parts):
    template_string = "\n".join(parts["styles"])

    template_context = get_template_context(
        mutable_app=mutable_app,
        mutable_request=mutable_request,
    )

    return Template(template_string).render(
        **template_context,
    )


def _render_scripts(mutable_app, mutable_request, parts):
    template_string = "\n".join([
        FALK_CLIENT_SCRIPT,
        *parts["scripts"],
        FALK_INIT_SCRIPT,
    ])

    # dump settings, tokens, and initial callbacks
    # If the request is a mutation request, we don't need to serialize the
    settings_string = ""
    token_string = ""
    callback_string = ""

    if not mutable_request["is_mutation_request"]:
        settings_string = json.dumps({
            "websockets": mutable_app["settings"]["websockets"],
        })

        token_string = json.dumps(parts["tokens"])
        callback_string = json.dumps(parts["callbacks"])

    # generate template context
    template_context = get_template_context(
        mutable_app=mutable_app,
        mutable_request=mutable_request,
        extra_template_context={
            "settings_string": settings_string,
            "token_string": token_string,
            "callback_string": callback_string,
        },
    )

    return Template(template_string).render(
        **template_context,
    )


def render_body(mutable_app, mutable_request, parts):
    return (
        _render_styles(
            mutable_app=mutable_app,
            mutable_request=mutable_request,
            parts=parts,
        ) +
        parts["html"] +
        _render_scripts(
            mutable_app=mutable_app,
            mutable_request=mutable_request,
            parts=parts,
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
        exception=None,
        is_root=True,
        run_component_callback="",
        parts=None,
):

    # TODO: add dependency caching once `uncachable_dependencies`
    # is implemented.

    if parts is None:
        parts = {
            "html": "",
            "styles": [],
            "scripts": [],
            "callbacks": [],
            "tokens": {},
            "flags": {
                "state": True,
            },
        }

    else:
        # reset component local flags
        parts["flags"]["state"] = True

    # check component
    if not callable(component):
        component_import_string = get_import_string(component)

        raise InvalidComponentError(
            f"{component_import_string}: components have to be callable",
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

    # setup callbacks, dependencies, and template context
    component_callbacks = {

        # This is a simple NOP to make calls like
        # `{{ falk.run_callback('render') }}` for simply re rendering work.
        "render": lambda: None,
    }

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
        "callbacks": component_callbacks,
        "response": response,
        "exception": exception,
    }

    template_context = get_template_context(
        mutable_app=mutable_app,
        mutable_request=request,
        extra_template_context=data,
        parts=parts,
        callbacks=component_callbacks,

        # TODO: we inspect the component at least twice here.
        # Explicitly using `get_dependencies()` and inexplicitly
        # using `run_callback()`.
        components=get_dependencies(component)[1],
    )

    dependencies = {
        **data,
        "template_context": template_context,
    }

    # run component
    try:
        component_template = run_callback(
            callback=component,
            dependencies=dependencies,
            providers=mutable_app["settings"]["dependencies"],
            run_coroutine_sync=mutable_app["settings"]["run_coroutine_sync"],
        )

    # TODO: Because we catch FalkErrors here, no component name is shown when
    # an error like ForbiddenError is raised, which makes debugging annoying.
    except FalkError:
        raise

    except Exception as exception:
        component_import_string = get_import_string(component)

        raise ComponentExecutionError(
            f"{component_import_string}: {repr(exception)}",
        ) from exception

    if not component_template:
        component_template = ""

    # Check if the component finished the response. If so, we can skip all
    # parsing and post processing.
    # This happens when files, binary data, or JSON is returned.
    if response["is_finished"]:
        return parts

    # `run_component_callback` is set to string that points to a callback
    # registered by the component component when we receive a mutation request.
    # The callback needs to run before we render the jinja2 template because
    # it will most likely mutate the template context.
    if run_component_callback:
        settings = mutable_app["settings"]

        dependencies.update({
            "args": request["json"].get("callbackArgs", []),
            "event": request["json"].get("event", {"form_data": {}}),
        })

        if run_component_callback not in component_callbacks:
            component_import_string = get_import_string(component)

            raise BadRequestError(
                f"{component_import_string}: unknown callback '{run_component_callback}'",  # NOQA
            )

        try:
            run_callback(
                callback=component_callbacks[run_component_callback],
                dependencies=dependencies,
                providers=settings["dependencies"],
                run_coroutine_sync=settings["run_coroutine_sync"],
            )

        # TODO: Because we catch FalkErrors here, no component name is shown
        # when an error like ForbiddenError is raised, which makes
        # debugging annoying.
        except FalkError:
            raise

        except Exception as exception:
            component_import_string = get_import_string(component)

            raise ComponentExecutionError(
                f"{component_import_string}::{run_component_callback}: {repr(exception)}",  # NOQA
            ) from exception

    # parse component template
    def _hash_string(string):
        return mutable_app["settings"]["hash_string"](
            mutable_app=mutable_app,
            string=string,
        )

    component_blocks = parse_component_template(
        component_template=component_template,
        component=component,
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
    if not token and parts["flags"]["state"]:
        component_id = mutable_app["settings"]["get_component_id"](
            component=component,
            mutable_app=mutable_app,
        )

        token = mutable_app["settings"]["encode_token"](
            component_id=component_id,
            data=component_state,
            mutable_app=mutable_app,
        )

        parts["tokens"][node_id] = token

    template_context["_token"] = token

    # render jinja2 template
    try:
        template = Template(component_blocks["jinja2_template"])
        parts["html"] = template.render(template_context)

    # TODO: Because we catch FalkErrors here, no component name is shown when
    # an error like ForbiddenError is raised, which makes debugging annoying.
    except FalkError:
        raise

    except Exception as exception:
        component_import_string = get_import_string(component)

        raise ComponentTemplatingError(
            f"{component_import_string}: {repr(exception)}",
        ) from exception

    # finish
    return parts

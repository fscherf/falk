import logging
import time

from falk.errors import UnknownComponentIdError, InvalidTokenError
from falk.rendering import render_component, render_body
from falk.immutable_proxy import get_immutable_proxy
from falk.dependency_injection import run_callback
from falk.http import set_header, set_status
from falk.routing import get_component
from falk.components import ItWorks

access_logger = logging.getLogger("falk.access")
error_logger = logging.getLogger("falk.errors")


def get_request(
        protocol="HTTP",
        headers=None,
        method="GET",
        path="/",
        content_type="",
        query=None,
        post=None,
        json=None,
):

    request = {
        # basic HTTP fields
        "protocol": protocol,
        "headers": {},
        "method": method,
        "path": path,
        "content_type": content_type,
        "query": query or {},
        "post": post or {},
        "json": json or {},

        # mutation
        "is_mutation_request": False,
        "callback_name": "",
        "callback_args": {},
        "event": {},
        "node_id": "",
        "token": "",
    }

    # headers
    for name, value in (headers or {}).items():
        set_header(
            headers=request["headers"],
            name=name,
            value=value,
        )

    # mutation requests
    if (request["method"] == "POST" and
            request["content_type"] == "application/json" and
            request["json"].get("requestType", "") == "falk/mutation"):

        request["is_mutation_request"] = True
        request["callback_name"] = request["json"]["callbackName"]
        request["callback_args"] = request["json"]["callbackArgs"]
        request["event"] = request["json"]["event"]
        request["node_id"] = request["json"]["nodeId"]
        request["token"] = request["json"]["token"]

    return request


def get_response(
        headers=None,
        status=200,
        charset="utf-8",
        content_type="text/html",
        body="",
        file_path="",
        json=None,
):

    response = {
        # basic HTTP fields
        "headers": {},
        "status": status,
        "charset": charset,
        "content_type": content_type,
        "body": body,
        "file_path": file_path,
        "json": json,

        # flags
        "is_finished": False,
    }

    set_status(
        response=response,
        status=status,
    )

    for name, value in (headers or {}).items():
        set_header(
            headers=response["headers"],
            name=name,
            value=value,
        )

    return response


def run_middlewares(
        middlewares,
        request,
        response,
        mutable_app,
):

    dependencies = {
        # meta data
        "is_root": True,

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

        # explicitly mutable
        "mutable_app": mutable_app,
        "mutable_settings": mutable_app["settings"],
        "mutable_request": request,

        # mutable by design
        "response": response,
    }

    for middleware in middlewares:
        dependencies["caller"] = middleware

        run_callback(
            callback=middleware,
            dependencies=dependencies,
            providers=mutable_app["settings"]["providers"],
            run_coroutine_sync=mutable_app["settings"]["run_coroutine_sync"],
        )


def handle_request(request, mutable_app):
    # TODO: make logging configurable
    # TODO: add client host and user agent to logs

    start_time = time.perf_counter()
    response = get_response()
    component = None
    component_state = None
    parts = {}

    try:
        # pre component middlewares
        run_middlewares(
            middlewares=mutable_app["settings"]["pre_component_middlewares"],
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

        # we run the component code only if the response was not finished
        # by a middleware before.
        if not response["is_finished"]:

            # mutation request (JSON response)
            if request["is_mutation_request"]:

                try:
                    # decode token
                    component_id, component_state = (
                        mutable_app["settings"]["decode_token"](
                            token=request["token"],
                            mutable_app=mutable_app,
                        )
                    )

                    # get component from cache
                    component = mutable_app["settings"]["get_component"](
                        component_id=component_id,
                        mutable_app=mutable_app,
                    )

                except (InvalidTokenError, UnknownComponentIdError):
                    # When the app gets restarted and generates random
                    # `settings["token_key"]` and/or
                    # `settings["component_id_salt"]` these errors happen on
                    # clients which are sending mutatation requests to the new
                    # instance using tokens, the old app generated.
                    #
                    # Reloading fixes both errors, so we return an
                    # HTTP redirect.

                    response.update({
                        "is_finished": True,
                        "content_type": "application/json",
                        "json": {
                            "flags": {
                                "reload": True,
                                "skipRendering": False,
                                "forceRendering": False,
                            },
                            "body": "",
                        },
                    })

            # initial render (HTML response)
            # if no routes are configured, we default to the
            # `ItWorks` component
            else:
                component = ItWorks

                if mutable_app["routes"]:

                    # search for a matching route
                    component, match_info = get_component(
                        routes=mutable_app["routes"],
                        path=request["path"],
                    )

                    request["match_info"] = match_info

                    # falling back to the configured 404 component
                    if not component:
                        component = (
                            mutable_app["settings"]["error_404_component"]
                        )

            # render component
            if not response["is_finished"]:
                parts = render_component(
                    component=component,
                    mutable_app=mutable_app,
                    request=request,
                    response=response,
                    node_id=request["node_id"],
                    component_state=component_state,
                    run_component_callback=request["callback_name"],
                )

        # post component middlewares
        run_middlewares(
            middlewares=mutable_app["settings"]["post_component_middlewares"],
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

    except Exception as exception:
        error_logger.exception(
            "exception raised while processing %s %s",
            request["method"],
            request["path"],
        )

        # render error 500 component
        component = mutable_app["settings"]["error_500_component"]

        component_props = {
            "exception": exception,
        }

        parts = render_component(
            component=component,
            mutable_app=mutable_app,
            request=request,
            response=response,
            component_props=component_props,
        )

    # set response body
    if parts:
        if request["is_mutation_request"]:
            response["json"] = {
                "flags": {
                    "reload": False,
                    "skipRendering": parts["flags"]["skip_rendering"],
                    "forceRendering": parts["flags"]["force_rendering"],
                },
                "body": render_body(
                    app=mutable_app,
                    parts=parts,
                ),
                "callbacks": parts["callbacks"],
            }

        elif not response["is_finished"]:
            response["body"] = parts["html"]

    # access log
    end_time = time.perf_counter()
    total_time = end_time - start_time
    total_time_string = f"{total_time:.4f}s"
    action_string = "initial render"

    if request["is_mutation_request"]:
        if component:
            component_identifier = f"{component.__module__}.{component.__qualname__}"  # NOQA

        else:
            component_identifier = "UKNOWN"

        action_string = f"mutation: {component_identifier}:{request['node_id']}"  # NOQA

    access_logger.info(
        "%s/%s %s %s -- %s -- took %s",
        request["protocol"],
        request["method"],
        request["path"],
        response["status"],
        action_string,
        total_time_string,
    )

    return response

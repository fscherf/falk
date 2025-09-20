import logging
import time
import json

from falk.immutable_proxy import get_immutable_proxy
from falk.dependency_injection import run_callback
from falk.http import set_header, set_status
from falk.rendering import render_component
from falk.routing import get_component
from falk.components import ItWorks

access_logger = logging.getLogger("falk.access")
error_logger = logging.getLogger("falk.errors")


def get_request(
        headers=None,
        method="GET",
        path="/",
        content_type="",
        post=None,
        json=None,
):

    request = {
        "finished": False,
        "headers": {},
        "method": method,
        "path": path,
        "content_type": content_type,
        "post": post or {},
        "json": json or {},
    }

    for name, value in (headers or {}).items():
        set_header(
            headers=request["headers"],
            name=name,
            value=value,
        )

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
        "finished": False,
        "headers": {},
        "status": status,
        "charset": charset,
        "content_type": content_type,
        "body": body,
        "file_path": file_path,
        "json": json,
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
    # TODO: add support for style and script URLs to mutation requests

    start_time = time.perf_counter()
    response = get_response()

    is_mutation_request = (
        request["method"] == "POST" and
        request["content_type"] == "application/json"
    )

    component = None
    node_id = None
    component_state = None
    callback_name = ""

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
        if not response["finished"]:

            # mutation request (JSON response)
            if is_mutation_request:
                token = request["json"]["token"]
                node_id = request["json"]["nodeId"]
                callback_name = request["json"]["callbackName"]

                # decode token
                component_id, component_state = (
                    mutable_app["settings"]["decode_token"](
                        token=token,
                        mutable_app=mutable_app,
                    )
                )

                # get component from cache
                component = mutable_app["settings"]["get_component"](
                    component_id=component_id,
                    mutable_app=mutable_app,
                )

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
            html = render_component(
                component=component,
                mutable_app=mutable_app,
                request=request,
                response=response,
                node_id=node_id,
                component_state=component_state,
                run_component_callback=callback_name,
            )["html"]

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
            "mutation_request": is_mutation_request,
        }

        html = render_component(
            component=component,
            mutable_app=mutable_app,
            request=request,
            response=response,
            component_props=component_props,
        )["html"]

    # finish response
    if is_mutation_request:
        response["body"] = json.dumps({
            "html": html,
        })

        response["content_type"] = "application/json"

    elif not response["finished"]:
        response["body"] = html

    # access log
    end_time = time.perf_counter()
    total_time = end_time - start_time
    total_time_string = f"{total_time:.4f}s"
    action_string = "initial render"

    if is_mutation_request:
        action_string = f"mutation: {component.__module__}.{component.__qualname__}:{node_id}"  # NOQA

    access_logger.info(
        "%s %s %s -- %s -- took %s",
        request["method"],
        request["path"],
        response["status"],
        action_string,
        total_time_string,
    )

    return response

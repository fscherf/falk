import logging
import time
import json

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
):

    response = {
        "headers": {},
        "status": status,
        "charset": charset,
        "content_type": content_type,
        "body": body,
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


def handle_request(request, app):
    # TODO: make logging configurable
    # TODO: add client host and user agent to logs

    start_time = time.perf_counter()
    response = get_response()

    mutation_request = (
        request["method"] == "POST" and
        request["content_type"] == "application/json"
    )

    component = None
    node_id = None
    component_state = None
    callback_name = ""

    try:
        # mutation request (JSON response)
        if mutation_request:
            token = request["json"]["token"]
            node_id = request["json"]["nodeId"]
            callback_name = request["json"]["callbackName"]

            # decode token
            component_id, component_state = app["settings"]["decode_token"](
                token=token,
                settings=app["settings"],
            )

            # get component from cache
            component = app["settings"]["get_component"](
                component_id=component_id,
                app=app,
            )

        # initial render (HTML response)
        # if no routes are configured, we default to the `ItWorks` component
        else:
            component = ItWorks

            if app["routes"]:

                # search for a matching route
                component, match_info = get_component(
                    routes=app["routes"],
                    path=request["path"],
                )

                request["match_info"] = match_info

                # falling back to the configured 404 component
                if not component:
                    component = app["settings"]["error_404_component"]

        # render component
        html = render_component(
            component=component,
            app=app,
            request=request,
            response=response,
            node_id=node_id,
            component_state=component_state,
            run_component_callback=callback_name,
        )

    except Exception as exception:
        error_logger.exception(
            "exception raised while processing %s %s",
            request["method"],
            request["path"],
        )

        # render error 500 component
        component = app["settings"]["error_500_component"]

        component_props = {
            "exception": exception,
            "mutation_request": mutation_request,
        }

        html = render_component(
            component=component,
            app=app,
            request=request,
            response=response,
            component_props=component_props,
        )

    # finish response
    if mutation_request:
        response["body"] = json.dumps({
            "html": html,
        })

        response["content_type"] = "application/json"

    else:
        response["body"] = html

    # access log
    end_time = time.perf_counter()
    total_time = end_time - start_time
    total_time_string = f"{total_time:.4f}s"
    action_string = "initial render"

    if mutation_request:
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

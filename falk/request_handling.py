import json

from falk.http import set_header, set_status
from falk.rendering import render_component
from falk.routing import get_component
from falk.components import ItWorks


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
    response = get_response()

    # mutation request (JSON response)
    if (request["method"] == "POST" and
            request["content_type"] == "application/json"):

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

        # encode response as json
        response["body"] = json.dumps({
            "html": html,
        })

        response["content_type"] = "application/json"

        return response

    # initial render (HTML response)
    # if no routes are configured, we default to the `ItWorks` component
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

    html = render_component(
        component=component,
        app=app,
        request=request,
        response=response,
    )

    response["body"] = html

    return response

import json

from falk.rendering import render_component
from falk.components import ItWorks


def get_request(
        headers=None,
        method="GET",
        path="/",
        content_type="",
        post=None,
        json=None,
):

    # TODO: normalize headers

    return {
        "headers": headers or {},
        "method": method,
        "path": path,
        "content_type": content_type,
        "post": post or {},
        "json": json or {},
    }


def get_response(
        headers=None,
        status=200,
        charset="utf-8",
        content_type="text/html",
        body="",
):

    # TODO: check status
    # TODO: normalize headers

    return {
        "headers": headers or {},
        "status": status,
        "charset": charset,
        "content_type": content_type,
        "body": body,
    }


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
    html = render_component(
        component=ItWorks,
        app=app,
        request=request,
        response=response,
    )

    response["body"] = html

    return response

from http.cookies import SimpleCookie
import logging

from falk.errors import HTTPError, BadRequestError, NotFoundError
from falk.rendering import render_component, render_body
from falk.immutable_proxy import get_immutable_proxy
from falk.dependency_injection import run_callback
from falk.routing import get_component
from falk.components import ItWorks

logger = logging.getLogger("falk")


def get_request():
    return {
        # scope
        "headers": {},
        "cookie": SimpleCookie(),
        "scheme": "http",
        "root_path": "",
        "raw_path": "",
        "path": "",
        "method": "GET",
        "query": {},
        "client": None,
        "server": None,

        # body
        "post": {},
        "json": {},
        "files": {},

        # flags
        "is_mutation_request": False,

        # user defined
        "user": None,
        "state": {},
    }


def get_response():
    return {
        # basic HTTP fields
        "headers": {},
        "cookie": SimpleCookie(),
        "status": 200,
        "charset": "utf-8",
        "content_type": "text/html",

        "body": "",
        "file_path": "",
        "json": None,

        # flags
        "is_finished": False,

        # user defined
        "state": {},
    }


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


def run_component(
        component,
        mutable_app,
        request,
        response,
        **kwargs,
):

    parts = render_component(
        component=component,
        mutable_app=mutable_app,
        request=request,
        response=response,
        **kwargs,
    )

    if response["is_finished"]:
        return

    if request["is_mutation_request"]:
        response["json"] = {
            "flags": {
                "reload": False,
                "skipRendering": parts["flags"]["skip_rendering"],
                "forceRendering": parts["flags"]["force_rendering"],
            },
            "body": render_body(
                app=mutable_app,
                request=request,
                parts=parts,
            ),
            "callbacks": parts["callbacks"],
        }

    else:
        response["body"] = parts["html"]


def handle_request(mutable_app, request, exception=None):
    response = get_response()
    component_state = None

    try:

        # Re raise exceptions that were catched while parsing the request.
        # This ensures that error components get called correctly.
        if exception:
            raise exception

        run_middlewares(
            middlewares=mutable_app["settings"]["pre_component_middlewares"],
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

        if not response["is_finished"]:

            # mutation requests
            if request["is_mutation_request"]:

                for key in ("token", "nodeId"):
                    if key not in request["json"]:
                        raise BadRequestError(f"no {key} provided")

                # decode token
                component_id, component_state = (
                    mutable_app["settings"]["decode_token"](
                        token=request["json"]["token"],
                        mutable_app=mutable_app,
                    )
                )

                # get component from cache
                component = mutable_app["settings"]["get_component"](
                    component_id=component_id,
                    mutable_app=mutable_app,
                )

            # initial render
            else:
                component = ItWorks

                if mutable_app["routes"]:

                    # search for a matching route
                    component, match_info = get_component(
                        routes=mutable_app["routes"],
                        path=request["path"],
                    )

                    request["match_info"] = match_info

                # no component found
                if not component:
                    raise NotFoundError()

            run_component(
                component=component,
                mutable_app=mutable_app,
                request=request,
                response=response,
                node_id=request["json"].get("nodeId", ""),
                component_state=component_state,
                run_component_callback=request["json"].get("callbackName", ""),
            )

        # post component middlewares
        run_middlewares(
            middlewares=(
                mutable_app["settings"]["post_component_middlewares"]
            ),
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

    except Exception as exception:
        if isinstance(exception, HTTPError):
            status = exception.STATUS.value
            error_component = mutable_app["settings"][exception.COMPONENT_NAME]

        else:
            logger.exception("exception raised while handling request")

            status = 500

            error_component = (
                mutable_app["settings"]["internal_server_error_component"]
            )

        # reset response
        response.update({
            "is_finished": False,
            "content_type": "text/html",
            "body": None,
            "file_path": "",
            "json": None,
        })

        if not request["is_mutation_request"]:
            response["status"] = status

        # run error component
        run_component(
            component=error_component,
            mutable_app=mutable_app,
            request=request,
            response=response,
            exception=exception,
        )

    return response

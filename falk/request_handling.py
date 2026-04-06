from http.cookies import SimpleCookie
import logging

from falk.rendering import render_component, render_body
from falk.immutable_proxy import get_immutable_proxy
from falk.dependency_injection import run_callback
from falk.routing import get_component
from falk.components import ItWorks

from falk.errors import (
    InvalidTokenError,
    BadRequestError,
    NotFoundError,
    HTTPError,
)

logger = logging.getLogger("falk")


def get_request():
    return {
        # scope
        "headers": {},
        "cookie": SimpleCookie(),
        "client": None,
        "server": None,
        "scheme": "http",
        "root_path": "",
        "raw_path": "",
        "method": "GET",
        "path": "",
        "query": {},
        "match_info": {},

        # body
        "post": {},
        "json": {},
        "files": {},
        "exception": None,

        # flags
        "valid": True,
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

    # TODO: When an error is raised in an middleware, the middleware name is
    # not in the error message.

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
            providers=mutable_app["settings"]["dependencies"],
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
            },
            "body": render_body(
                mutable_app=mutable_app,
                mutable_request=request,
                parts=parts,
            ),
            "tokens": parts["tokens"],
            "callbacks": parts["callbacks"],
        }

    else:
        response["body"] = parts["html"]


def run_error_component(
        exception,
        mutable_app,
        request,
        response,
):

    # When we encounter an `InvalidTokenError` while processing a mutation
    # request, chances are that we got this request from a valid client,
    # that has state from before we restarted.
    # In this case, we just ask the client to reload the page to get new
    # tokens issued.
    #
    # TODO: add test
    if (isinstance(exception, InvalidTokenError) and
            request["is_mutation_request"]):

        response.update({
            "is_finished": True,
            "json": {
                "flags": {
                    "reload": True,
                },
            },
        })

        return response

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


def handle_request(mutable_app, request):
    response = get_response()
    component_state = None

    try:

        # pre request middlewares
        #
        # The request can be invalid and raise an exception in the next stage.
        # We still run the pre request middlewares though to give the app an
        # opportunity to do some logging or telemetry.
        run_middlewares(
            middlewares=mutable_app["settings"]["pre_request_middlewares"],
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

        # Re raise exceptions that were catched while parsing the request.
        # This ensures that error components get called correctly.
        if request["exception"]:
            raise request["exception"]

        # pre component middlewares
        run_middlewares(
            middlewares=mutable_app["settings"]["pre_component_middlewares"],
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

        # Components and post component middlewares only run if the response
        # was not finished in a pre component middleware. This happens for
        # static files for example.
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
        run_error_component(
            exception=exception,
            mutable_app=mutable_app,
            request=request,
            response=response,
        )

    # post request middlewares
    #
    # Post request middlewares run in their own try catch block so we can
    # ensure that no matter where in the pipeline an exception was raised,
    # these middlewares run, to give the app an opportunity to do logging,
    # telemetry, or close database connections.
    try:
        run_middlewares(
            middlewares=mutable_app["settings"]["post_request_middlewares"],
            request=request,
            response=response,
            mutable_app=mutable_app,
        )

    except Exception as exception:
        run_error_component(
            exception=exception,
            mutable_app=mutable_app,
            request=request,
            response=response,
        )

    return response

import json

from starlette.responses import JSONResponse, FileResponse, Response
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException

from falk.request_handling2 import get_request, handle_request
from falk.http import set_header, get_header
from falk.errors import InvalidRequestError


async def _parse_multipart_request(mutable_app, request, starlette_request):
    token = get_header(
        headers=request["headers"],
        name="X-Falk-Upload-Token",
        default="",
    )

    if token:
        component_id, data = mutable_app["settings"]["decode_token"](
            token=token,
            mutable_app=mutable_app,
        )

        if component_id not in mutable_app["components"]:
            raise InvalidRequestError(f"Unknown component ID: {component_id}")

    else:
        data = {
            "max_files": 0,
            "max_file_size": 0,
        }

    form_kwargs = {
        # defaults taken from https://starlette.dev/requests/#request-files
        "max_fields": 1000,
        "max_files": data["max_files"],
        "max_part_size": data["max_file_size"],
    }

    try:
        async with starlette_request.form(**form_kwargs) as form:
            for key, value in form.items():

                # mutation request data
                if key == "falk/mutation":
                    request["json"] = json.loads(value)

                # files
                if isinstance(value, UploadFile):
                    request["files"][key] = value

                # form data
                else:
                    request["post"][key] = form.getlist(key)

    except HTTPException as starlette_exception:
        if not token:
            raise InvalidRequestError(
                "Upload token is not set",
            ) from starlette_exception

        else:
            raise InvalidRequestError(
                starlette_exception.detail,
            ) from starlette_exception


async def handle_starlette_request(mutable_app, starlette_request):

    # setup request
    request = get_request()
    exception = None

    request["method"] = starlette_request.method
    request["path"] = starlette_request.url.path

    for key in starlette_request.query_params.keys():
        request["query"][key.strip()] = (
            starlette_request.query_params.getlist(key)
        )

    for name, value in starlette_request.headers.items():
        set_header(
            request["headers"],
            name=name,
            value=value,
        )

    try:
        content_type = get_header(
            headers=request["headers"],
            name="content-type",
            default="",
        )

        request_type = get_header(
            headers=request["headers"],
            name="x-falk-request-type",
            default="",
        )

        if request_type == "mutation":
            request["is_mutation_request"] = True

        # POST
        if starlette_request.method == "POST":

            # JSON
            if content_type == "application/json":
                request["json"] = await starlette_request.json()

            # multipart
            else:
                await _parse_multipart_request(
                    mutable_app=mutable_app,
                    request=request,
                    starlette_request=starlette_request,
                )

    except Exception as _exception:
        exception = _exception

    # generate response
    response = await run_in_threadpool(
        lambda: handle_request(
            mutable_app=mutable_app,
            request=request,
            exception=exception,
        ),
    )

    # generate starlette response from falk response
    if response["json"]:
        return JSONResponse(
            response["json"],
            headers=response["headers"],
            status_code=response["status"],
            media_type=response["content_type"],
        )

    elif response["file_path"]:
        return FileResponse(
            response["file_path"],
            headers=response["headers"],
            status_code=response["status"],
        )

    else:
        return Response(
            response["body"],
            headers=response["headers"],
            status_code=response["status"],
            media_type=response["content_type"],
        )

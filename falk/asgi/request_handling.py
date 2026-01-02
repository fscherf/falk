from urllib.parse import parse_qs
import asyncio
import json

from falk.request_handling2 import get_request, handle_request
from falk.asgi.file_responses import handle_file_response
from falk.asgi.multipart import handle_multipart_body
from falk.http import set_header, get_header
from falk.errors import InvalidRequestError
from falk.asgi.helper import get_body


async def handle_http_request(mutable_app, event, scope, receive, send):
    loop = asyncio.get_event_loop()

    # setup request
    request = get_request()
    exception = None

    request["method"] = scope["method"]
    request["path"] = scope["path"]
    request["query"] = parse_qs(scope["query_string"].decode())

    for name, value in scope.get("headers", []):
        set_header(
            request["headers"],
            name=name.decode(),
            value=value.decode(),
        )

    try:
        content_type = get_header(
            headers=request["headers"],
            name="content-type",
            default="",
        )

        content_length = get_header(
            headers=request["headers"],
            name="content-length",
            default="0",
        )

        request_type = get_header(
            headers=request["headers"],
            name="x-falk-request-type",
            default="",
        )

        if not content_length.isnumeric():
            raise InvalidRequestError(
                "header Content-Length has to be a number",
            )

        content_length = int(content_length)

        if request_type == "mutation":
            request["is_mutation_request"] = True

        # POST
        if scope["method"] == "POST":

            # JSON
            if content_type == "application/json":
                body = await get_body(
                    event=event,
                    receive=receive,
                    content_length=content_length,
                )

                request["json"] = json.loads(body)

            # URL encoded
            # TODO: remove obsolete support for URL encoded POST
            elif content_type == "application/x-www-form-urlencoded":
                body = await get_body(
                    event=event,
                    receive=receive,
                    content_length=content_length,
                )

                request["post"] = parse_qs(body.decode())

            # multipart
            elif content_type.startswith("multipart/form-data;"):
                await handle_multipart_body(
                    mutable_app=mutable_app,
                    request=request,
                    content_type=content_type,
                    content_length=content_length,
                    event=event,
                    scope=scope,
                    receive=receive,
                )

    except Exception as _exception:
        exception = _exception

    # handle falk request
    response = await loop.run_in_executor(
        mutable_app["executor"],
        lambda: handle_request(
            mutable_app=mutable_app,
            request=request,
            exception=exception,
        ),
    )

    # send response
    # file responses
    if response["file_path"]:
        await handle_file_response(
            response=response,
            send=send,
        )

    # JSON / binary / text responses
    else:
        headers = [
            (name.encode(), value.encode())
            for name, value in response["headers"].items()
        ]

        if response["json"]:
            body = json.dumps(response["json"])

        else:
            body = response["body"]

        if isinstance(body, str):
            body = body.encode()

        await send({
            "type": "http.response.start",
            "status": response["status"],
            "headers": headers,
        })

        await send({
            "type": "http.response.body",
            "body": body,
        })

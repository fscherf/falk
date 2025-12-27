from urllib.parse import parse_qs
import asyncio
import json

from falk.asgi.file_responses import handle_file_response
from falk.request_handling import get_request
from falk.http import get_header, set_header


def _handle_falk_request(mutable_app, scope, body):

    # setup request
    query = parse_qs(scope["query_string"].decode())
    headers = {}

    for name, value in scope.get("headers", []):
        set_header(
            headers=headers,
            name=name.decode("utf-8"),
            value=value.decode("utf-8"),
        )

    content_type = get_header(
        headers=headers,
        name="Content-Type",
        default="",
    )

    content_length = get_header(
        headers=headers,
        name="Content-Length",
        default="0",
    )

    request_kwargs = {
        "protocol": "HTTP",
        "headers": headers,
        "method": scope["method"],
        "path": scope["path"],
        "content_type": content_type,
        "query": query,
    }

    if scope["method"] == "POST":
        if content_length.isnumeric():
            content_length = int(content_length)
            body = body[0:content_length].decode("utf-8")

            if content_type == "application/json":
                request_kwargs["json"] = json.loads(body)

            elif content_type == "application/x-www-form-urlencoded":
                request_kwargs["post"] = parse_qs(body)

    request = get_request(**request_kwargs)

    # handle request
    response = mutable_app["entry_points"]["handle_request"](
        request=request,
        mutable_app=mutable_app,
    )

    # encode response
    if response["json"]:
        response["body"] = json.dumps(response["json"])

    set_header(
        headers=response["headers"],
        name="content-length",
        value=str(len(response["body"].encode("utf-8"))),
    )

    response["headers"] = [
        (k.encode(), v.encode()) for k, v in response["headers"].items()
    ]

    response["body"] = response["body"].encode()

    return response


async def handle_http_request(mutable_app, event, scope, receive, send):
    loop = asyncio.get_event_loop()

    # read body
    body = event.get("body", b"")

    while event.get("more_body", False):
        event = await receive()

        body += event.get("body", b"")

    # handle request
    response = await loop.run_in_executor(
        mutable_app["executor"],
        lambda: _handle_falk_request(mutable_app, scope, body),
    )

    if response["file_path"]:
        await handle_file_response(
            response=response,
            send=send,
        )

    else:
        await send({
            "type": "http.response.start",
            "status": response["status"],
            "headers": response["headers"],
        })

        await send({
            "type": "http.response.body",
            "body": response["body"],
        })

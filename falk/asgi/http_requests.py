import asyncio
import json

from falk.asgi.file_responses import handle_file_response


def get_response(mutable_app, request):
    response = mutable_app["entry_points"]["handle_request"](
        mutable_app=mutable_app,
        request=request,
    )

    # encode headers
    response["headers"] = [
        (name.encode(), value.encode())
        for name, value in response["headers"].items()
    ]

    # handle JSON responses
    if response["json"]:
        response["body"] = json.dumps(response["json"])

    # encode body
    if isinstance(response["body"], str):
        response["body"] = response["body"].encode()

    return response


async def handle_http_request(mutable_app, event, scope, receive, send):
    loop = asyncio.get_event_loop()

    request = await parse_http_request(
        mutable_app=mutable_app,
        event=event,
        scope=scope,
        receive=receive,
    )

    response = await loop.run_in_executor(
        mutable_app["executor"],
        lambda: get_response(
            mutable_app=mutable_app,
            request=request,
        ),
    )

    # file response
    if response["file_path"]:
        await handle_file_response(
            response=response,
            send=send,
        )

    # binary/text responses
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

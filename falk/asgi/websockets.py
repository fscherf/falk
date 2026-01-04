from urllib.parse import parse_qs
import asyncio
import json

from falk.request_handling import get_request, handle_request
from falk.http import set_header


def _handle_websocket_message(mutable_app, scope, text):

    # setup request
    request = get_request()
    exception = None

    request["path"] = scope["path"]
    request["query"] = parse_qs(scope["query_string"].decode())

    for name, value in scope.get("headers", []):
        set_header(
            request["headers"],
            name=name.decode(),
            value=value.decode(),
        )

    # we only accept mutation requests as websocket messages
    request["is_mutation_request"] = True

    try:
        message_id, message_data = json.loads(text)

        request["json"] = message_data

    except Exception as _exception:
        exception = _exception

    response = handle_request(
        mutable_app=mutable_app,
        request=request,
        exception=exception,
    )

    return json.dumps([message_id, response])


async def handle_websocket(mutable_app, scope, receive, send):
    loop = asyncio.get_event_loop()

    while True:
        event = await receive()

        # websocket.connect
        if event["type"] == "websocket.connect":
            if mutable_app["settings"]["websockets"]:
                await send({"type": "websocket.accept"})

            else:
                await send({"type": "websocket.close"})

        # websocket.disconnect
        elif event["type"] == "websocket.disconnect":
            break

        # websocket.receive
        elif event["type"] == "websocket.receive":
            response_string = await loop.run_in_executor(
                mutable_app["executor"],
                lambda: _handle_websocket_message(
                    mutable_app=mutable_app,
                    scope=scope,
                    text=event["text"],
                ),
            )

            await send({
                "type": "websocket.send",
                "text": response_string,
            })

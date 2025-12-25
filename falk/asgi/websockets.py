from urllib.parse import parse_qs
import asyncio
import json

from falk.request_handling import get_request


def _handle_websocket_message(mutable_app, scope, text):

    # setup request
    request_id, json_data = json.loads(text)
    query = parse_qs(scope["query_string"].decode())
    headers = {}

    for name, value in scope.get("headers", []):
        headers[name.decode("utf-8")] = value.decode("utf-8")

    request = get_request(
        protocol="WS",
        headers=headers,
        method="POST",
        path=scope["path"],
        content_type="application/json",
        query=query,
        json=json_data,
    )

    # handle request
    response = mutable_app["entry_points"]["handle_request"](
        request=request,
        mutable_app=mutable_app,
    )

    return json.dumps([request_id, response])


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

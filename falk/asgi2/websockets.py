from starlette.concurrency import run_in_threadpool

from falk.request_handling2 import get_request, handle_request
from falk.http import set_header


async def handle_websocket(mutable_app, websocket):
    await websocket.accept()

    # headers
    headers = {}

    for name, value in websocket.headers.items():
        set_header(
            headers=headers,
            name=name,
            value=value,
        )

    # query
    query = {}

    for key in websocket.query_params.keys():
        query[key] = websocket.query_params.getlist(key)

    async for message in websocket.iter_json():
        message_id, message_data = message
        request = get_request()

        # all websocket requests are mutation requests by definition
        request["is_mutation_request"] = True

        request["headers"] = headers.copy()
        request["method"] = "GET"
        request["path"] = websocket.url.path
        request["query"] = query.copy()
        request["json"] = message_data

        response = await run_in_threadpool(
            lambda: handle_request(
                mutable_app=mutable_app,
                request=request,
            ),
        )

        await websocket.send_json([message_id, response])

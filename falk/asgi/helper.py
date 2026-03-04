async def get_body_chunks(event, receive):
    chunk = event.get("body", b"")

    yield chunk

    while event.get("more_body", False):
        event = await receive()
        chunk = event.get("body", b"")

        yield chunk


async def get_body(event, receive):
    body = b""

    iterator = get_body_chunks(
        event=event,
        receive=receive,
    )

    async for chunk in iterator:
        body += chunk

    return body

from falk.errors import BadRequestError


async def get_body_chunks(event, receive, content_length):
    chunk = event.get("body", b"")
    read_bytes = len(chunk)

    def _check_content_length():
        if read_bytes > content_length:
            raise BadRequestError("body exceeds content length")

    _check_content_length()

    yield chunk

    while event.get("more_body", False):
        event = await receive()
        chunk = event.get("body", b"")
        read_bytes += len(chunk)

        _check_content_length()

        yield chunk


async def get_body(event, receive, content_length):
    body = b""

    iterator = get_body_chunks(
        event=event,
        receive=receive,
        content_length=content_length,
    )

    async for chunk in iterator:
        body += chunk

    return chunk

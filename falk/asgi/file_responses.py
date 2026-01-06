import mimetypes
import os

import aiofiles

CHUNK_SIZE = 64 * 1024  # 64 KiB


async def handle_file_response(response, send):
    # TODO: set statuscode, headers, and cookies correctly

    abs_path = response["file_path"]
    rel_path = os.path.basename(abs_path)
    file_size = os.path.getsize(abs_path)
    mime = mimetypes.guess_type(abs_path)[0] or "application/octet-stream"

    headers = [
        (b"content-type", mime.encode()),

        (b"content-disposition",
         f'attachment; filename="{rel_path}"'.encode()),

        (b"content-length", str(file_size).encode()),
    ]

    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": headers,
    })

    bytes_sent = 0

    async with aiofiles.open(abs_path, "rb") as f:
        while True:
            chunk = await f.read(CHUNK_SIZE)

            if not chunk:
                break

            bytes_sent += len(chunk)
            more_body = bytes_sent < file_size

            await send({
                "type": "http.response.body",
                "body": chunk,
                "more_body": more_body,
            })

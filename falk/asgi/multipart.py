import json

from multipart.multipart import parse_options_header
from multipart import MultipartParser

from falk.dependency_injection import get_dependencies, run_callback
from falk.errors import BadRequestError, UnknownComponentIdError
from falk.immutable_proxy import get_immutable_proxy
from falk.asgi.helper import get_body_chunks
from falk.http import get_header


def run_file_upload_handler(
        handler,
        handler_dependencies,
        handler_state,
        mutable_app,
        request,
        event,
        name,
        filename,
        chunk,
):

    return run_callback(
        callback=handler,
        dependencies={
            "event": event,
            "name": name,
            "filename": filename,
            "chunk": chunk,
            "upload_state": handler_state,

            # immutable
            "app": get_immutable_proxy(
                data=mutable_app,
                name="app",
                mutable_version_name="mutable_app",
            ),

            "settings": get_immutable_proxy(
                data=mutable_app["settings"],
                name="settings",
                mutable_version_name="mutable_settings",
            ),

            "request": get_immutable_proxy(
                data=request,
                name="request",
                mutable_version_name="mutable_request",
            ),

            # explicitly mutable
            "mutable_app": mutable_app,
            "mutable_settings": mutable_app["settings"],
            "mutable_request": request,
        },
        get_dependencies=lambda *args, **kwargs: handler_dependencies,
        run_coroutine_sync=mutable_app["settings"]["run_coroutine_sync"],
    )


async def handle_multipart_body(
        mutable_app,
        request,
        content_type,
        content_length,
        event,
        scope,
        receive,
):

    # find component from header X-Falk-Upload-Token
    component_id = get_header(
        headers=request["headers"],
        name="X-Falk-Upload-Token",
        default="",
    )

    if not component_id:
        raise BadRequestError("X-Falk-Upload-Token header is not set")

    try:
        mutable_app["settings"]["get_component"](
            component_id=component_id,
            mutable_app=mutable_app,
        )

    except UnknownComponentIdError as exception:
        raise BadRequestError("Uknown component id") from exception

    # find file upload component
    handler = mutable_app["settings"]["get_file_upload_handler"](
        component_id=component_id,
        mutable_app=mutable_app,
    )

    handler_dependencies = get_dependencies(handler)

    # parse multipart body
    current_part = {}
    handler_state = {}

    def on_part_begin():
        current_part.update({
            "headers": {},
            "current_header_field": b"",
            "current_header_value": b"",
            "current_field_name": "",
            "current_field_value": b"",
            "current_file_name": "",
        })

    def on_header_field(data, start, end):
        current_part["current_header_field"] += data[start:end]

    def on_header_value(data, start, end):
        current_part["current_header_value"] += data[start:end]

    def on_header_end():
        field = current_part["current_header_field"].decode().lower()
        value = current_part["current_header_value"].decode().lower()

        current_part["headers"][field] = value
        current_part["current_header_field"] = b""
        current_part["current_header_value"] = b""

    def on_headers_finished():
        disposition = current_part["headers"].get("content-disposition", "")

        if not disposition:
            return

        _, params = parse_options_header(disposition.encode())
        field_name = params.get(b"name", b"").decode()
        file_name = params.get(b"filename", b"").decode()

        current_part["current_field_name"] = field_name
        current_part["current_file_name"] = file_name

    def on_part_data(data, start, end):
        chunk = data[start:end]

        # files
        if current_part["current_file_name"]:
            run_file_upload_handler(
                handler=handler,
                handler_dependencies=handler_dependencies,
                handler_state=handler_state,
                mutable_app=mutable_app,
                request=request,
                event="chunk-read",
                name=current_part["current_field_name"],
                filename=current_part["current_file_name"],
                chunk=chunk,
            )

        # form-data
        else:
            current_part["current_field_value"] += chunk

    def on_part_end():
        chunk = b""

        # files
        if current_part["current_file_name"]:
            run_file_upload_handler(
                handler=handler,
                handler_dependencies=handler_dependencies,
                handler_state=handler_state,
                mutable_app=mutable_app,
                request=request,
                event="chunk-read",
                name=current_part["current_field_name"],
                filename=current_part["current_file_name"],
                chunk=chunk,
            )

        # form-data
        else:
            try:
                request["json"] = json.loads(
                    current_part["current_field_value"].decode(),
                )

            except json.decoder.JSONDecodeError:
                # This happens if a file field was left empty by the user.
                # In this case we have no filename and no valid JSON.

                pass

    _, params = parse_options_header(content_type)
    boundary = params.get(b"boundary")

    parser = MultipartParser(boundary, {
        "on_part_begin": on_part_begin,
        "on_header_field": on_header_field,
        "on_header_value": on_header_value,
        "on_header_end": on_header_end,
        "on_headers_finished": on_headers_finished,
        "on_part_data": on_part_data,
        "on_part_end": on_part_end,
    })

    chunks = get_body_chunks(
        event=event,
        receive=receive,
        content_length=content_length,
    )

    run_file_upload_handler(
        handler=handler,
        handler_dependencies=handler_dependencies,
        handler_state=handler_state,
        mutable_app=mutable_app,
        request=request,
        event="upload-start",
        name="",
        filename="",
        chunk=b"",
    )

    async for chunk in chunks:
        parser.write(chunk)

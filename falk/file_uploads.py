import tempfile
import logging
import os

from falk.errors import BadRequestError

logger = logging.getLogger("falk.file-uploads")


def default_file_upload_handler():
    # reject all files
    raise BadRequestError("component does not accept file uploads")


def get_tempfile_upload_handler(
        max_files=0,
        max_file_size_in_bytes=1024 * 1000,  # 1GB
):

    def tempfile_upload_handler(
            mutable_request,
            upload_state,
            event,
            name,
            filename,
            chunk,
    ):

        # gets called when the upload starts
        if event == "upload-start":
            mutable_request["_file_upload_state"] = {
                "temp_dir": tempfile.TemporaryDirectory(),
                "files_written": 0,
                "bytes_written": {},
                "file_handles": {},
            }

        # gets called on every read chunk
        elif event == "chunk-read":
            upload_state = mutable_request["_file_upload_state"]

            # open new file
            if name not in upload_state["file_handles"]:

                # check if new file exceeds `max_files`
                if upload_state["files_written"] + 1 > max_files:
                    raise BadRequestError(
                        f"max_files of {max_files} exceeded",
                    )

                abs_path = os.path.join(
                    upload_state["temp_dir"].name,
                    filename,
                )

                upload_state["file_handles"][name] = open(abs_path, "wb+")
                upload_state["files_written"] += 1
                upload_state["bytes_written"][name] = 0

                # register file in the request for the component to use
                mutable_request["files"][name] = abs_path

            # write chunks to file system
            if chunk:

                # check if chunk exceeds `max_file_size_in_bytes`
                bytes_written = upload_state["bytes_written"][name]
                file_handle = upload_state["file_handles"][name]

                if bytes_written + len(chunk) > max_file_size_in_bytes:
                    file_handle.close()

                    raise BadRequestError(
                        f'file "{name}" ({filename}) exceeds the size limit of {max_file_size_in_bytes} bytes',  # NOQA
                    )

                file_handle.write(chunk)

            # an empty chunk means that the file is fully uploaded
            else:
                file_handle = upload_state["file_handles"].pop(name)

                file_handle.close()

    return tempfile_upload_handler

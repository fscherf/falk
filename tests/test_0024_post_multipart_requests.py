import pytest


@pytest.mark.parametrize("args", [
    # form 1: 1 file, 1024 bytes (valid)
    {
        "html_id": "form-1",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 1024,
                "md5": "c9a34cfc85d982698c6ac89f76071abd",
            },
        },
        "error_message_parts": [],
    },

    # form 1: 1 files, 2048 bytes (invalid)
    {
        "html_id": "form-1",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 2048,
            },
        },
        "error_message_parts": [
            "Error 400:",
            '"file-1" (file-1.txt) exceeds the size limit of 1024 bytes',
        ],
    },

    # form 1: 2 files, 1024 bytes (invalid)
    {
        "html_id": "form-1",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 1024,
                "md5": "c9a34cfc85d982698c6ac89f76071abd",
            },
            "file-2": {
                "filename": "file-2.txt",
                "size": 1024,
                "md5": "c9a34cfc85d982698c6ac89f76071abd",
            },
        },
        "error_message_parts": [
            "Error 400:",
            "max_files of 1 exceeded",
        ],
    },

    # form 2: 2 file, 1024 bytes (valid)
    {
        "html_id": "form-2",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 1024,
                "md5": "c9a34cfc85d982698c6ac89f76071abd",
            },
            "file-2": {
                "filename": "file-2.txt",
                "size": 1024,
                "md5": "c9a34cfc85d982698c6ac89f76071abd",
            },
        },
        "error_message_parts": [],
    },

    # form 2: 2 file, 1024 bytes and 2048 bytes (invalid)
    {
        "html_id": "form-2",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 1024,
            },
            "file-2": {
                "filename": "file-2.txt",
                "size": 2048,
            },
        },
        "error_message_parts": [
            "Error 400:",
            '"file-2" (file-2.txt) exceeds the size limit of 1024 bytes',
        ],
    },

    # form 3: no token (invalid)
    {
        "html_id": "form-3",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 1024,
            },
        },
        "error_message_parts": [
            "Error 400:",
            "X-Falk-Upload-Token header is not set",
        ],
    },

    # form 3: no handler (invalid)
    {
        "html_id": "form-4",
        "form_data": {
            "field-1": "value-1",
            "field-2": "value-2",
        },
        "file_data": {
            "file-1": {
                "filename": "file-1.txt",
                "size": 1024,
            },
        },
        "error_message_parts": [
            "Error 400:",
            "component does not accept file uploads",
        ],
    },
])
def test_post_multipart_requests(args, page, start_falk_app):
    """
    This test tests file uploads using `/request-handling/multipart-forms`
    in the test app.
    """

    import tempfile
    import json
    import os

    from test_app.app import configure_app

    _, base_url = start_falk_app(
        configure_app=configure_app,
    )

    html_id = args["html_id"]

    def get_values(page):
        return {
            "text_field": page.input_value("input[name=text_field]"),
            "number_field": page.input_value("input[name=number_field]"),

            "textarea_field":
                page.input_value("textarea[name=textarea_field]"),

            "select_field": page.input_value("select[name=select_field]"),
        }

    # run test
    with tempfile.TemporaryDirectory() as root:

        # go to form
        url = base_url + "/request-handling/multipart-forms"

        page.goto(url)
        page.wait_for_selector("h2:text('Multipart Forms')")

        # setup files
        for name, value in args["file_data"].items():
            abs_path = os.path.join(root, value["filename"])

            with open(abs_path, "w+") as file_handle:
                file_handle.write("a" * value["size"])

            with page.expect_file_chooser() as fc_info:
                page.click(f"#{html_id} input[name={name}]")

                fc_info.value.set_files(abs_path)

        # form data
        for name, value in args["form_data"].items():
            page.fill(f"#{html_id} input[name={name}]", value)

        # submit
        page.click(f"#{html_id} input[type=submit]")

        # errors
        if args["error_message_parts"]:
            error_message = page.text_content("div.falk-error")

            for error_message_part in args["error_message_parts"]:
                assert error_message_part in error_message

        else:

            # form data
            form_data = json.loads(
                page.text_content("pre#form-data.filled"),
            )

            assert form_data == args["form_data"]

            # file data
            file_data = json.loads(
                page.text_content("pre#file-data.filled"),
            )

            assert file_data == args["file_data"]

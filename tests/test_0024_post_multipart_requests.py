import pytest


@pytest.mark.parametrize("args", [
    {
        "token": 1,
        "max_files": 2,
        "max_file_size": 2048,
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
        "error_message_parts": [],
    },

    # no token provided
    {
        "token": 0,
        "max_files": 1,
        "max_file_size": 2048,
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
            "Upload token is not set",
        ],
    },

    # max_files exceeded
    {
        "token": 1,
        "max_files": 1,
        "max_file_size": 2048,
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
            "Too many files.",
        ],
    },
])
def test_post_multipart_requests(args, page, start_falk_app):
    from urllib.parse import urlencode
    import tempfile
    import json
    import os

    from test_app.app import configure_app

    _, base_url = start_falk_app(
        configure_app=configure_app,
        interface="asgi2",
    )

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

        query_string = urlencode({
            "token": args["token"],
            "max_files": args["max_files"],
            "max_file_size": args["max_file_size"],
        }, doseq=True)

        page.goto(f"{url}?{query_string}")
        page.wait_for_selector("h2:text('Multipart Forms')")

        # setup files
        for name, value in args["file_data"].items():
            abs_path = os.path.join(root, value["filename"])

            with open(abs_path, "w+") as file_handle:
                file_handle.write("a" * value["size"])

            with page.expect_file_chooser() as fc_info:
                page.click(f"input[name={name}]")

                fc_info.value.set_files(abs_path)

        # form data
        for name, value in args["form_data"].items():
            page.fill(f"input[name={name}]", value)

        # submit
        page.click("input[type=submit]")

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

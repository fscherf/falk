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
            "400 Bad Request:",
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
            "400 Bad Request:",
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
            "400 Bad Request:",
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
            "400 Bad Request:",
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
            "400 Bad Request:",
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

    _, base_url, _ = start_falk_app(
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


@pytest.mark.only_browser("chromium")
def test_malicious_file_names(page, start_falk_app, tmp_path):
    """
    This test tries to upload a file into a temporary directory that was
    created by this test, not by falk, outside any safe locations.

    If this succeeds, the test is failed.
    """

    from pathlib import Path

    import requests

    from test_app.app import configure_app

    # We need a valid upload token first. The easiest way to get a valid one
    # is to spin up the test project, go to `/request-handling/multipart-forms`
    # and extract it from the form.
    _, base_url, _ = start_falk_app(configure_app=configure_app)
    form_url = base_url + "/request-handling/multipart-forms"

    page.goto(form_url)
    page.wait_for_selector("h2:text('Multipart Forms')")

    upload_token = page.locator(
        "#form-1 input[name='falk/upload-token']",
    ).get_attribute("value")

    # sub path
    rel_path = Path("some-directory/pwned.txt")
    abs_path = tmp_path / rel_path

    response = requests.post(
        form_url,
        files={
            "file-1": (str(rel_path), b"pwned", "text/plain"),
        },
        headers={
            "X-Falk-Request-Type": "mutation",
            "X-Falk-Upload-Token": upload_token,
        },
    )

    assert "400 Bad Request:" in response.text
    assert not abs_path.exists()

    # absolute path
    abs_path = tmp_path / "pwned.txt"

    response = requests.post(
        form_url,
        files={
            "file-1": (str(abs_path), b"pwned", "text/plain"),
        },
        headers={
            "X-Falk-Request-Type": "mutation",
            "X-Falk-Upload-Token": upload_token,
        },
    )

    assert "400 Bad Request:" in response.text
    assert not abs_path.exists()

    # relative path
    rel_path = Path("../../app/pwned.txt")
    abs_path = Path("/app/pwned.txt")

    response = requests.post(
        form_url,
        files={
            "file-1": (str(rel_path), b"pwned", "text/plain"),
        },
        headers={
            "X-Falk-Request-Type": "mutation",
            "X-Falk-Upload-Token": upload_token,
        },
    )

    assert "400 Bad Request:" in response.text
    assert not abs_path.exists()

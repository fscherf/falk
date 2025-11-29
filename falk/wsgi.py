from wsgiref.util import FileWrapper
from urllib.parse import parse_qs
from http import HTTPStatus
import json

from falk.request_handling import get_request
from falk.apps import run_configure_app


def get_http_status_string(status_code):
    status = HTTPStatus(status_code)

    return f"{status_code} {status.name}"


def get_request_from_wsgi_environ(environ):
    content_type = environ.get("CONTENT_TYPE", "")

    request_kwargs = {
        "protocol": "HTTP",
        "method": environ["REQUEST_METHOD"],
        "path": environ["PATH_INFO"],
        "content_type": content_type,
        "query": parse_qs(environ["QUERY_STRING"]),
    }

    # POST
    if environ["REQUEST_METHOD"] == "POST":
        content_length = environ.get("CONTENT_LENGTH", "0")
        body = b""

        if content_length.isnumeric():
            content_length = int(content_length)
            body = environ["wsgi.input"].read(content_length)

            if content_type == "application/json":
                request_kwargs["json"] = json.loads(body.decode("utf-8"))

            elif content_type == "application/x-www-form-urlencoded":
                body_string = body.decode("utf-8")
                request_kwargs["post"] = parse_qs(body_string)

    return get_request(**request_kwargs)


def get_wsgi_app(configure_app, lazy=False):
    mutable_app = {}

    def setup_app():
        mutable_app.update(
            run_configure_app(configure_app),
        )

    if not lazy:
        setup_app()

    def wsgi_app(environ, start_response):
        if not mutable_app:
            setup_app()

        request = get_request_from_wsgi_environ(
            environ=environ,
        )

        response = mutable_app["entry_points"]["handle_request"](
            request=request,
            mutable_app=mutable_app,
        )

        # start response
        headers = []

        if response["json"]:
            response["body"] = json.dumps(response["json"])

        body = response["body"].encode("utf-8")

        for key, value in response["headers"].items():
            headers.append(
                (key, value, ),
            )

        if not response["file_path"]:

            # content type
            content_type_string = f'{response["content_type"]}; charset=utf-8'

            headers.append(
                ("content-type", content_type_string),
            )

            # content_length
            headers.append(
                ("content-length", str(len(body))),
            )

        start_response(
            get_http_status_string(
                status_code=response["status"],
            ),
            headers,
        )

        # file responses
        if response["file_path"]:
            file_handle = open(response["file_path"], "rb")

            return FileWrapper(file_handle)

        # text responses
        return [body]

    return wsgi_app

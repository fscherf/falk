from falk.http import set_status, get_header, set_header, del_header
from falk.utils.path import get_abs_path


# status
def set_response_status_provider(response):
    def set_response_status(status):
        set_status(
            response=response,
            status=status,
        )

    return set_response_status


# headers
def get_response_header_provider(response):
    def get_response_header(name, default=None):
        return get_header(
            headers=response["headers"],
            name=name,
            default=default,
        )

    return get_response_header


def set_response_header_provider(response):
    def set_response_header(name, value):
        set_header(
            headers=response["headers"],
            name=name,
            value=value,
        )

    return set_response_header


def del_response_header_provider(response):
    def del_response_header(name):
        del_header(
            headers=response["headers"],
            name=name,
        )

    return del_response_header


# content
def set_response_content_type_provider(response):
    def set_response_content_type(content_type):
        if not isinstance(content_type, str):
            raise RuntimeError(
                "content types need to be strings",
            )

        response["content_type"] = content_type

    return set_response_content_type


def set_response_body_provider(response):
    def set_respones_body(response_body):
        response["body"] = response_body
        response["is_finished"] = True

    return set_respones_body


def set_response_file_provider(response, caller, is_root):
    def set_response_file(path):
        if not is_root:
            raise RuntimeError(
                "set_response_file can only be used in root components",
            )

        abs_path = get_abs_path(
            caller=caller,
            path=path,
            require_file=True,
        )

        response["file_path"] = abs_path
        response["is_finished"] = True

    return set_response_file


def set_response_json_provider(response, is_root):
    def set_response_json(data):
        if not is_root:
            raise RuntimeError(
                "set_response_json can only be used in root components",
            )

        response["json"] = data
        response["is_finished"] = True

    return set_response_json

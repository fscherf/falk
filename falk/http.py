from falk.errors import InvalidStatusCodeError


def set_status(response, status):
    if 100 < status > 599:
        raise InvalidStatusCodeError(
            "HTTP status codes have to be between 100 and 599",
        )

    response["status"] = status

from falk.errors import InvalidStatusCodeError


# status
def set_status(response, status):
    if 100 < status > 599:
        raise InvalidStatusCodeError(
            "HTTP status codes have to be between 100 and 599",
        )

    response["status"] = status


# headers
def normalize_header_name(name):
    return name.title()


def set_header(headers, name, value):
    normalized_header_name = normalize_header_name(name)

    headers[normalized_header_name] = value


def get_header(headers, name, default=None):
    normalized_header_name = normalize_header_name(name)

    if default is not None:
        return headers.get(normalized_header_name, default)

    return headers.get(normalized_header_name)


def del_header(headers, name, value):
    normalized_header_name = normalize_header_name(name)

    del headers[normalized_header_name]

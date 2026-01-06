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


# cookies
def set_cookie(simple_cookie, name, **attributes):
    value = attributes.pop("value", "")

    simple_cookie[name] = value

    for key, value in attributes.items():
        simple_cookie[name][key] = value


def get_cookie(simple_cookie, name):
    # NOTE: we rename keys like `max-age` to `max_age` to make the return value
    # of this function usable as the attributes for `set_cookie`
    #
    # cookie = get_cookie("foo")
    # cookie["max_age"] = 3600
    # set_cookie("foo", **cookie)

    morsel = simple_cookie.get(name)

    # empty cookie
    if not morsel:
        return {
            "value": "",
            "comment": "",
            "domain": "",
            "expires": "",
            "httponly": "",
            "max_age": "",
            "path": "",
            "samesite": "",
            "secure": "",
            "version": "",
        }

    morsel_data = {
        "value": morsel.value,
    }

    for key, value in morsel.items():
        key = key.replace("-", "_")

        morsel_data[key] = value

    return morsel_data


def del_cookie(simple_cookie, name):
    del simple_cookie[name]

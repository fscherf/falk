from falk.http import (
    get_header,
    set_header,
    del_header,
    get_cookie,
    set_cookie,
    del_cookie,
)


# headers
def get_request_header_provider(mutable_request):
    def get_request_header(name, default=None):
        return get_header(
            headers=mutable_request["headers"],
            name=name,
            default=default,
        )

    return get_request_header


def set_request_header_provider(muatable_request):
    def set_request_header(name, value):
        set_header(
            headers=muatable_request["headers"],
            name=name,
            value=value,
        )

    return set_request_header


def del_request_header_provider(mutable_request):
    def del_request_header(name):
        del_header(
            headers=mutable_request["headers"],
            name=name,
        )

    return del_request_header


# cookies
def get_request_cookie_provider(request):
    def get_request_cookie(name):
        return get_cookie(
            simple_cookie=request["cookie"],
            name=name,
        )

    return get_request_cookie


def set_request_cookie_provider(request):
    def set_request_cookie(name, **attributes):
        return set_cookie(
            simple_cookie=request["cookie"],
            name=name,
            **attributes,
        )

    return set_request_cookie


def del_request_cookie_provider(request):
    def del_request_cookie(name):
        return del_cookie(
            simple_cookie=request["cookie"],
            name=name,
        )

    return del_request_cookie

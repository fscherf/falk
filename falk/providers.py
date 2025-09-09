from falk.http import set_status, get_header, set_header, del_header
from falk.routing import get_route


# response status
def set_response_status_provider(response):
    def set_response_status(status):
        set_status(
            response=response,
            status=status,
        )

    return set_response_status


# request headers
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


# response_headers
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


# routes
def add_route_provider(app):
    def add_route(pattern, component, name=""):
        app["routes"].append(
            get_route(
                pattern=pattern,
                component=component,
                name=name,
            ),
        )

    return add_route

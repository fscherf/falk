from falk.http import set_status, get_header, set_header, del_header


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

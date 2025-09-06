from falk.http import set_status


def set_response_status_provider(response):
    def set_response_status(status):
        set_status(
            response=response,
            status=status,
        )

    return set_response_status

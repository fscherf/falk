def _check_middleware(middleware):
    if not callable(middleware):
        raise ValueError("middlewares need to be callable")


def add_pre_request_middleware_provider(mutable_settings):
    def add_pre_request_middleware(middleware):
        _check_middleware(middleware)

        mutable_settings["pre_request_middlewares"].append(middleware)

    return add_pre_request_middleware


def add_post_request_middleware_provider(mutable_settings):
    def add_post_request_middleware(middleware):
        _check_middleware(middleware)

        mutable_settings["post_request_middlewares"].append(middleware)

    return add_post_request_middleware


def add_pre_component_middleware_provider(mutable_settings):
    def add_pre_component_middleware(middleware):
        _check_middleware(middleware)

        mutable_settings["pre_component_middlewares"].append(middleware)

    return add_pre_component_middleware


def add_post_component_middleware_provider(mutable_settings):
    def add_post_component_middleware(middleware):
        _check_middleware(middleware)

        mutable_settings["post_component_middlewares"].append(middleware)

    return add_post_component_middleware

def add_pre_component_middleware_provider(mutable_app):
    def add_pre_component_middleware(middleware):
        mutable_app["settings"]["pre_component_middlewares"].append(middleware)

    return add_pre_component_middleware


def add_post_component_middleware_provider(mutable_app):
    def add_post_component_middleware(middleware):
        mutable_app["settings"]["post_component_middlewares"].append(middleware)

    return add_post_component_middleware

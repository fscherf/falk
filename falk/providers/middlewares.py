def add_pre_component_middleware_provider(app):
    def add_pre_component_middleware(middleware):
        app["pre_component_middlewares"].append(middleware)

    return add_pre_component_middleware


def add_post_component_middleware_provider(app):
    def add_post_component_middleware(middleware):
        app["post_component_middlewares"].append(middleware)

    return add_post_component_middleware

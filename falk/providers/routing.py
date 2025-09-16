from falk.routing import get_route


def add_route_provider(mutable_app):
    def add_route(pattern, component, name=""):
        mutable_app["routes"].append(
            get_route(
                pattern=pattern,
                component=component,
                name=name,
            ),
        )

    return add_route

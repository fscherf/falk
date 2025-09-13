from falk.routing import get_route


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

from falk import routing


def add_route_provider(mutable_app):
    def add_route(pattern, component, name=""):
        mutable_app["routes"].append(
            routing.get_route(
                pattern=pattern,
                component=component,
                name=name,
            ),
        )

    return add_route


def get_url_provider(app):
    def get_url(route_name, route_args=None, query=None, checks=True):
        return routing.get_url(
            routes=app["routes"],
            route_name=route_name,
            route_args=route_args,
            query=query,
            checks=checks,
        )

    return get_url

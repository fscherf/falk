from falk import routing

from jinja2 import pass_context


@pass_context
def get_url(context, route_name, route_args=None, query=None, checks=True):
    return routing.get_url(
        routes=context["app"]["routes"],
        route_name=route_name,
        route_args=route_args,
        query=query,
        checks=checks,
    )

from urllib.parse import urlencode
import re

from falk.errors import (
    InvalidRouteArgsError,
    InvalidRouteError,
    UnknownRouteError,
    InvalidPathError,
)

PARTS_RE = re.compile(r"<(?P<name>[^:>]+)(:(?P<pattern>[^>]+))?>")
ROUTE_PART_FORMAT_STRING = r"(?P<{}>{})"
DEFAULT_PART_PATTERN = r"[^/]+"
OPTIONAL_TRAILING_SLASH_PATTERN = r"(/)"


def get_route(pattern, component, name=""):
    if not pattern.startswith("/"):
        raise InvalidRouteError(
            'all routes have to start with a "/"',
        )

    # optional trailing slash
    optional_trailing_slash = False

    if pattern.endswith(OPTIONAL_TRAILING_SLASH_PATTERN):
        optional_trailing_slash = True
        pattern = pattern[:-len(OPTIONAL_TRAILING_SLASH_PATTERN)]

    # parse pattern
    groups = PARTS_RE.findall(pattern)
    cleaned_pattern = PARTS_RE.sub("{}", pattern)
    parts = []

    for part_name, _, part_pattern in groups:
        parts.append(
            (part_name, part_pattern or DEFAULT_PART_PATTERN),
        )

    # setup pattern_re
    pattern_re = re.compile(
        r"^{}{}$".format(
            cleaned_pattern.format(
                *[ROUTE_PART_FORMAT_STRING.format(*pattern)
                  for pattern in parts],
            ),
            r"(/)?" if optional_trailing_slash else "",
        ),
    )

    # setup format string
    format_string = cleaned_pattern.format(
        *["{" + name + "}" for name, _ in parts]
    )

    if optional_trailing_slash:
        format_string += "/"

    return (
        pattern_re,
        component,
        format_string,
        name,
    )


def get_component(routes, path):
    if not path.startswith("/"):
        raise InvalidPathError(
            'all paths have to start with "/"',
        )

    for route in routes:
        pattern = route[0]
        match_object = pattern.match(path)

        if not match_object:
            continue

        return route[1], match_object.groupdict()

    return None, None


def get_url(routes, route_name, route_args=None, query=None, checks=True):

    # find route by name
    route = None

    for _route in routes:
        if _route[3] == route_name:
            route = _route

    if not route:
        raise UnknownRouteError(f'no route with name "{route_name}" found')

    pattern_re, _, format_string, _ = route

    # run format string
    try:
        url = format_string.format(**(route_args or {}))

    except KeyError as exception:
        raise InvalidRouteArgsError(
            f"missing arguments: {exception.args[0]}"
        )

    # run checks
    if checks and not pattern_re.match(url):
        raise InvalidRouteArgsError(
            f"format string: {repr(format_string)}, args: {repr(route_args)}",
        )

    # append URL query
    if query:
        query_string = urlencode(query, doseq=True)

        url = f"{url}?{query_string}"

    return url

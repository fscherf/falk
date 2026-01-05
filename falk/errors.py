from http import HTTPStatus


class FalkError(Exception):
    pass


# settings
class InvalidSettingsError(FalkError):
    pass


# dependency injection
class DependencyError(FalkError):
    pass


class UnknownDependencyError(DependencyError):
    pass


class CircularDependencyError(DependencyError):
    pass


class InvalidDependencyProviderError(DependencyError):
    pass


class AsyncNotSupportedError(DependencyError):
    pass


# tokens
class InvalidTokenError(FalkError):
    pass


# HTML
class HTMLError(FalkError):
    pass


class InvalidStyleBlockError(HTMLError):
    pass


class InvalidScriptBlockError(HTMLError):
    pass


class MissingRootNodeError(HTMLError):
    pass


class MultipleRootNodesError(HTMLError):
    pass


class UnbalancedTagsError(HTMLError):
    pass


class UnclosedTagsError(HTMLError):
    pass


# components
class ComponentError(FalkError):
    pass


class UnknownComponentError(ComponentError):
    pass


class InvalidComponentError(ComponentError):
    pass


class UnknownComponentIdError(ComponentError):
    pass


class InvalidStatusCodeError(ComponentError):
    pass


# HTTP
class HTTPError(FalkError):
    STATUS = HTTPStatus.INTERNAL_SERVER_ERROR
    COMPONENT_NAME = "internal_server_error_component"


class BadRequestError(HTTPError):
    STATUS = HTTPStatus.BAD_REQUEST
    COMPONENT_NAME = "bad_request_error_component"


class ForbiddenError(HTTPError):
    STATUS = HTTPStatus.FORBIDDEN
    COMPONENT_NAME = "forbidden_error_component"


class NotFoundError(HTTPError):
    STATUS = HTTPStatus.NOT_FOUND
    COMPONENT_NAME = "not_found_error_component"


# routing
class RoutingError(FalkError):
    pass


class UnknownRouteError(RoutingError):
    pass


class InvalidRouteError(RoutingError):
    pass


class InvalidPathError(RoutingError):
    pass


class InvalidRouteArgsError(RoutingError):
    pass

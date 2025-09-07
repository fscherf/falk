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


# HTTP
class HTTPError(FalkError):
    pass


class InvalidStatusCodeError(HTTPError):
    pass


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

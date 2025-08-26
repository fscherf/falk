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

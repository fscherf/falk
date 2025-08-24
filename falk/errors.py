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

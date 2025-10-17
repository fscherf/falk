import asyncio
import inspect

from falk.errors import (
    InvalidDependencyProviderError,
    CircularDependencyError,
    UnknownDependencyError,
    AsyncNotSupportedError,
)


def get_dependencies(callback):
    required_dependencies = []
    dependencies = {}

    parameters = inspect.signature(callback).parameters

    for name, parameter in parameters.items():
        if parameter.default is inspect.Parameter.empty:
            required_dependencies.append(name)

        else:
            dependencies[name] = parameter.default

    return required_dependencies, dependencies


def run_coroutine_sync(coroutine):
    # Since we know, we created this coroutine and can never await it we can
    # close it to avoid `coroutine was never awaited` warnings.
    coroutine.close()

    raise AsyncNotSupportedError()


def format_dependencies(items):
    formated_items = []

    for item in items:
        if callable(item):
            formated_items.append(
                f"{item.__module__}.{item.__qualname__}",
            )

        else:
            formated_items.append(item)

    return " -> ".join(formated_items)


def run_callback(
        callback,
        dependencies=None,
        providers=None,
        cache=None,
        get_dependencies=get_dependencies,
        run_coroutine_sync=run_coroutine_sync,
        _stack=None,
):

    # TODO: replace `dependencies` and `providers` with `dependencies` and
    # `uncachable_dependencies` which both should be implemented as
    # providers (callbacks).
    # With the current model, providers with dependencies like `caller`, which
    # need to be re evaluated on every call, not only per request, don't work
    # if dependency caching is enabled.

    dependencies = dependencies or {}
    providers = providers or {}
    _stack = _stack or []

    # We need to be very specific here because it is important that we use the
    # exact same object for the entire tree of dependencies.
    # `cache = cache or {}` would override the cache with every node that
    # yields no cached values.
    if cache is None:
        cache = {}

    # inspect callback
    required_dependencies, _ = get_dependencies(callback=callback)

    # search for unknown dependencies
    for name in required_dependencies:
        if name not in providers and name not in dependencies:
            raise UnknownDependencyError(
                format_dependencies([callback, name])
            )

    callback_dependencies = {}

    for name in required_dependencies:

        # dependencies
        # We prefer directly injected dependencies over provider dependencies
        # here because `dependencies` will be used for tightly scoped variables
        # like `request` or `response`.
        if name in dependencies:
            callback_dependencies[name] = dependencies[name]

            continue

        # providers
        # check if dependency was resolved before
        if name in cache:
            callback_dependencies[name] = cache[name]

            continue

        # providers need to be callable
        if not callable(providers[name]):
            raise InvalidDependencyProviderError(providers[name])

        # if we try to resolve a dependency that is already on the stack
        # we know we encountered a circular dependency
        if name in _stack:
            raise CircularDependencyError(
                format_dependencies([*_stack, name])
            )

        # run provider
        dependency = run_callback(
            callback=providers[name],
            providers=providers,
            dependencies=dependencies,
            cache=cache,
            get_dependencies=get_dependencies,
            run_coroutine_sync=run_coroutine_sync,
            _stack=_stack + [name],
        )

        callback_dependencies[name] = dependency
        cache[name] = dependency

    # run callback
    return_value = callback(**callback_dependencies)

    if asyncio.iscoroutine(return_value):
        return run_coroutine_sync(return_value)

    return return_value

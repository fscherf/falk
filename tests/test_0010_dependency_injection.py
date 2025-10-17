import pytest


def test_get_dependencies():
    from falk.dependency_injection import get_dependencies

    def callback1(arg_1, arg_2, arg_3, arg_4="value"):
        pass  # pragma: no cover

    assert get_dependencies(
        callback=callback1,
    ) == (
        ["arg_1", "arg_2", "arg_3"],
        {"arg_4": "value"},
    )


def test_run_callback():
    from falk.dependency_injection import run_callback
    from falk.errors import UnknownDependencyError

    def valid_callback1(arg_1, arg_2):
        return [arg_1, arg_2]

    def valid_callback2(arg_2, arg_1):
        return [arg_1, arg_2]

    def valid_callback3(arg_1, arg_2, arg_3):
        return [arg_1, arg_2, arg_3]

    def invalid_callback1(arg_1, arg_2, arg_3, arg_4):
        pass  # pragma: no cover

    def invalid_callback2(arg_1, *args, **kwargs):
        pass  # pragma: no cover

    def invalid_callback3(*args, **kwargs):
        pass  # pragma: no cover

    dependencies = {
        "arg_1": 1,
        "arg_2": 2,
        "arg_3": 3,
    }

    # valid callbacks
    assert run_callback(
        callback=valid_callback1,
        dependencies=dependencies,
    ) == [1, 2]

    assert run_callback(
        callback=valid_callback2,
        dependencies=dependencies,
    ) == [1, 2]

    assert run_callback(
        callback=valid_callback3,
        dependencies=dependencies,
    ) == [1, 2, 3]

    # invalid callbacks
    with pytest.raises(UnknownDependencyError):
        run_callback(
            callback=invalid_callback1,
            dependencies=dependencies,
        )

    with pytest.raises(UnknownDependencyError):
        run_callback(
            callback=invalid_callback2,
            dependencies=dependencies,
        )

    with pytest.raises(UnknownDependencyError):
        run_callback(
            callback=invalid_callback3,
            dependencies=dependencies,
        )


def test_dependency_name_caching():
    from falk.dependency_injection import run_callback
    from falk.errors import UnknownDependencyError

    def get_wrong_dependencies(callback):
        return ["arg_4"], {}

    def callback1(arg_1, arg_2, arg_3):
        pass  # pragma: no cover

    dependencies = {
        "arg_1": 1,
        "arg_2": 2,
        "arg_3": 3,
    }

    # valid dependency names
    run_callback(
        callback=callback1,
        dependencies=dependencies,
    )

    # invalid dependency names
    with pytest.raises(UnknownDependencyError):
        run_callback(
            callback=callback1,
            dependencies=dependencies,
            get_dependencies=get_wrong_dependencies,
        )


def test_dependency_providers():
    from falk.dependency_injection import run_callback

    def request_method_provider(request):
        return request["method"]

    def get_request_method_provider(request):
        def get_request_method():
            return request["method"]

        return get_request_method

    def run_test(request, request_method, get_request_method):
        assert request["method"] == "GET"
        assert request_method == "GET"
        assert get_request_method() == "GET"

        return "SUCCESS"

    return_value = run_callback(
        callback=run_test,
        dependencies={
            "request": {
                "method": "GET",
            },
        },
        providers={
            "request_method": request_method_provider,
            "get_request_method": get_request_method_provider,
        },
    )

    assert return_value == "SUCCESS"


def test_dependency_provider_caching():
    from falk.dependency_injection import run_callback

    call_count = [0]
    cache = {}

    def request_provider():
        call_count[0] += 1

        return "request"

    # first run
    run_callback(
        callback=lambda request: None,
        providers={
            "request": request_provider,
        },
        cache=cache,
    )

    assert call_count[0] == 1
    assert cache["request"] == "request"

    # second run
    run_callback(
        callback=lambda request: None,
        providers={
            "request": request_provider,
        },
        cache=cache,
    )

    assert call_count[0] == 1
    assert cache["request"] == "request"


def test_async_callbacks_and_providers(loop):
    import asyncio

    from falk.dependency_injection import run_callback
    from falk.errors import AsyncNotSupportedError

    def run_coroutine_sync(coroutine):
        future = asyncio.run_coroutine_threadsafe(
            coro=coroutine,
            loop=loop,
        )

        return future.result()

    # async callbacks
    async def handle_click(event):
        assert event == {"type": "click"}

        return "SUCCESS"

    with pytest.raises(AsyncNotSupportedError):
        run_callback(
            callback=handle_click,
            dependencies={
                "event": {
                    "type": "click",
                },
            },
        )

    return_value = run_callback(
        callback=handle_click,
        dependencies={
            "event": {
                "type": "click",
            },
        },
        run_coroutine_sync=run_coroutine_sync,
    )

    assert return_value == "SUCCESS"

    # async providers
    async def event_provider():
        return {"type": "click"}

    async def handle_click(event):
        assert event == {"type": "click"}

        return "SUCCESS 2"

    with pytest.raises(AsyncNotSupportedError):
        run_callback(
            callback=handle_click,
            providers={
                "event": event_provider,
            },
        )

    return_value = run_callback(
        callback=handle_click,
        providers={
            "event": event_provider,
        },
        run_coroutine_sync=run_coroutine_sync,
    )

    assert return_value == "SUCCESS 2"


def test_invalid_dependency_providers():
    from falk.errors import InvalidDependencyProviderError
    from falk.dependency_injection import run_callback

    with pytest.raises(InvalidDependencyProviderError):
        run_callback(
            callback=lambda request: None,
            providers={
                "request": "request",
            },
        )


def test_circular_dependencies():
    from falk.dependency_injection import run_callback
    from falk.errors import CircularDependencyError

    def request_provider(request):
        return request  # pragma: no cover

    def run_test(request):
        pass  # pragma: no cover

    with pytest.raises(CircularDependencyError):
        run_callback(
            callback=run_test,
            providers={
                "request": request_provider,
            },
        )

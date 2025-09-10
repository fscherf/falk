import asyncio


def configure_run_coroutine_sync(mutable_app):
    loop = asyncio.get_running_loop()

    def run_coroutine_sync(coroutine):
        future = asyncio.run_coroutine_threadsafe(
            coro=coroutine,
            loop=loop,
        )

        return future.result()

    mutable_app["settings"]["run_coroutine_sync"] = run_coroutine_sync

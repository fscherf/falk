def add_startup_callback_provider(mutable_app):
    def add_startup_callback(callback):
        if not callable(callable):
            raise ValueError("callback needs to be callable")

        mutable_app["entry_points"]["on_startup"].append(callback)

    return add_startup_callback


def add_shutdown_callback_provider(mutable_app):
    def add_shutdown_callback(callback):
        if not callable(callable):
            raise ValueError("callback needs to be callable")

        mutable_app["entry_points"]["on_shutdown"].append(callback)

    return add_shutdown_callback

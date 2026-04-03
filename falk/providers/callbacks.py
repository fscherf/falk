def add_callback_provider(callbacks):
    def add_callback(callback, name=""):
        if not callable(callback):
            raise ValueError("callback needs to be callable")

        name = name or callback.__name__

        callbacks[name] = callback

    return add_callback


def run_callback_provider(template_context, node_id):
    # TODO: add test for selectors
    # TODO: add test for delays

    def run_callback(
            callback_name,
            callback_args=None,
            selector="self",
            delay=0,
    ):

        if selector == "self":
            selector = f"[fx-id={node_id}]"

        if callback_args and not isinstance(callback_args, (dict, list)):
            raise ValueError("'callback_args' needs to be either dict or list")

        template_context["falk"]["_parts"]["callbacks"].append(
            [selector, callback_name, callback_args, delay],
        )

    return run_callback

def run_callback_provider(template_context, node_id):
    # TODO: add test for delays

    def run_callback(
            callback_name,
            callback_args=None,
            selector="self",
            delay=0,
    ):

        if selector == "self":
            selector = f"[data-falk-id={node_id}]"

        if callback_args and not isinstance(callback_args, (dict, list)):
            raise ValueError("'callback_args' needs to be either dict or list")

        template_context["_parts"]["callbacks"].append(
            [selector, callback_name, callback_args, delay],
        )

    return run_callback

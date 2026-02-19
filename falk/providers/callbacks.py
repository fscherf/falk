def run_callback_provider(template_context, node_id):
    def run_callback(selector, callback_name, callback_args=None):
        if selector == "self":
            selector = f"[data-falk-id={node_id}]"

        if callback_args and not isinstance(callback_args, (dict, list)):
            raise ValueError("'callback_args' needs to be either dict or list")

        template_context["_parts"]["callbacks"].append(
            [selector, callback_name, callback_args],
        )

    return run_callback

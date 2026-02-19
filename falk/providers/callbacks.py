def run_callback_provider(template_context, node_id):
    def run_callback(
            selector,
            callback_name,
            *callback_args,
            **callback_kwargs,
    ):

        if selector == "self":
            selector = f"[data-falk-id={node_id}]"

        if callback_args and callback_kwargs:
            raise ValueError(
                "args and kwargs can not be used at the same time",
            )

        template_context["_parts"]["callbacks"].append(
            [selector, callback_name, callback_args or callback_kwargs],
        )

    return run_callback

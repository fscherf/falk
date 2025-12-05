def run_callback_provider(context):
    def run_callback(
            selector,
            callback_name,
            *callback_args,
            **callback_kwargs,
    ):

        if callback_args and callback_kwargs:
            raise ValueError(
                "args and kwargs can not be used at the same time",
            )

        context["_parts"]["callbacks"].append(
            [selector, callback_name, callback_args or callback_kwargs],
        )

    return run_callback

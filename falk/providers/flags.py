def disable_state_provider(template_context):
    def disable_state(value=False):
        template_context["falk"]["_parts"]["flags"]["state"] = value

    return disable_state

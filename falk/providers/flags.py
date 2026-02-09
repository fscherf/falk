def skip_rendering_provider(template_context):
    def skip_rendering(value=True):
        template_context["_parts"]["flags"]["skip_rendering"] = value

    return skip_rendering


def force_rendering_provider(template_context):
    def force_rendering(value=True):
        template_context["_parts"]["flags"]["force_rendering"] = value

    return force_rendering


def disable_state_provider(template_context):
    def disable_state(value=False):
        template_context["_parts"]["flags"]["state"] = value

    return disable_state

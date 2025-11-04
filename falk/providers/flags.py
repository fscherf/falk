def skip_rendering_provider(context):
    def skip_rendering(value=True):
        context["_parts"]["flags"]["skip_rendering"] = value

    return skip_rendering


def force_rendering_provider(context):
    def force_rendering(value=True):
        context["_parts"]["flags"]["force_rendering"] = value

    return force_rendering

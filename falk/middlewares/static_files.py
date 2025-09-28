import os


def serve_static_files(
        request,
        response,
        settings,
        set_response_file,
        set_response_status,
        set_response_body,
):

    # NOTE: This needs to be a middleware because the prefix for static URLs
    # should be configurable in the settings (settings["static_url_prefix"]).

    if response["is_finished"]:
        return

    if not request["path"].startswith(settings["static_url_prefix"]):
        return

    rel_path = request["path"][len(settings["static_url_prefix"]):]

    if rel_path.startswith("/"):
        rel_path = rel_path[1:]

    for static_dir in settings["static_dirs"]:
        abs_path = os.path.join(
            static_dir,
            rel_path,
        )

        if not os.path.exists(abs_path):
            continue

        # matching file found
        set_response_file(abs_path)

        return

    # no matching file found
    set_response_status(404)

    # TODO: setting the status code to 404 should trigger the
    # Error404 component
    set_response_body("Error 404: Not found")

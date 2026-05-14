from falk.utils.path import resolve_path
from falk.errors import NotFoundError


def serve_static_files(request, response, settings, set_response_file):
    # NOTE: This needs to be a middleware because the prefix for static URLs
    # should be configurable in the settings (settings["static_url_prefix"]).

    if response["is_finished"]:
        return

    if not request["path"].startswith(settings["static_url_prefix"]):
        return

    rel_path = request["path"][len(settings["static_url_prefix"]):]

    try:
        abs_path = resolve_path(
            safe_base_paths=settings["static_dirs"],
            unsafe_path=rel_path,
            is_directory=False,
            exists=True,
        )

        set_response_file(abs_path)

    except FileNotFoundError as error:
        raise NotFoundError() from error

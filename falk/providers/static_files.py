from falk.static_files import get_static_url
from falk.utils.path import get_abs_path


def add_static_dir_provider(caller, mutable_settings):
    def add_static_dir(path):
        abs_path = get_abs_path(
            caller=caller,
            path=path,
            require_directory=True,
        )

        if abs_path in mutable_settings["static_dirs"]:
            return

        mutable_settings["static_dirs"].append(abs_path)

    return add_static_dir


def get_static_url_provider(settings, request):
    def _get_static_url(rel_path):
        return get_static_url(
            root_path=request["root_path"] or "/",
            static_url_prefix=settings["static_url_prefix"],
            rel_path=rel_path,
        )

    return _get_static_url

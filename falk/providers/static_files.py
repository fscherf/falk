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

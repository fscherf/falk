import os


def get_falk_static_dir():
    return os.path.join(
        os.path.dirname(__file__),
        "static",
    )


def get_static_url(root_path, static_url_prefix, rel_path):
    if static_url_prefix.startswith("/"):
        static_url_prefix = static_url_prefix[1:]

    if rel_path.startswith("/"):
        rel_path = rel_path[1:]

    return os.path.join(
        root_path,
        static_url_prefix,
        rel_path,
    )

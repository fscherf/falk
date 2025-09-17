import os


def get_falk_static_dir():
    return os.path.join(
        os.path.dirname(__file__),
        "static",
    )

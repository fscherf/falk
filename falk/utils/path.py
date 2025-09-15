import inspect
import os


def get_abs_path(caller, path, require_file=False, require_directory=False):
    abs_path = ""

    # path is an absolute path
    if path.startswith("/"):
        abs_path = path

    # path is relative to the caller
    else:
        callback_path = inspect.getfile(caller)
        callback_dirname = os.path.dirname(callback_path)
        abs_path = os.path.join(callback_dirname, path)

    # check if path exists
    if not os.path.exists(abs_path):
        raise FileNotFoundError(
            f"{caller.__name__}: {path} does not exist. Tried {abs_path}",
        )

    # check if path is a file
    if require_file and os.path.isdir(abs_path):
        raise IsADirectoryError(
            f"{caller.__name__}: {path} is a directory. Absolute path: {abs_path}",  # NOQA
        )

    # check if path is a directory
    if require_directory and not os.path.isdir(abs_path):
        raise NotADirectoryError(
            f"{caller.__name__}: {path} is not a directory. Absolute path: {abs_path}",  # NOQA
        )

    return abs_path

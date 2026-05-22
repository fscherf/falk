from pathlib import Path
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


def resolve_path(
        safe_base_paths,
        unsafe_path,
        is_directory=None,
        is_direct_child=None,
        exists=None,
):

    """
    Resolves an unsafe, user provided path, like a static URL, and resolves it
    against a list of safe base paths.
    If the unsafe path tries to leave one of the matching base paths,
    a `FileNotFoundError` is raised.

    All check flags are tri-states: If `exists` is set to `None`, no checks
    are executed. If set to `True`, the file needs to exist.
    """

    # clean unsafe path
    _unsafe_path = Path(unsafe_path.lstrip("/"))

    # run mandatory checks
    if is_direct_child is not None:
        parts = _unsafe_path.parts

        if is_direct_child and len(parts) > 1:
            raise FileNotFoundError(unsafe_path)

        if not is_direct_child and len(parts) < 2:
            raise FileNotFoundError(unsafe_path)

    for safe_base_path_string in safe_base_paths:
        safe_base_path = Path(safe_base_path_string).resolve()
        unsafe_abs_path = (safe_base_path / _unsafe_path).resolve()

        # run mandatory checks
        # check if the resolved path is a sub path of the safe base path
        if not unsafe_abs_path.is_relative_to(safe_base_path):
            continue

        # run extra checks
        _is_directory = unsafe_abs_path.is_dir()

        # check if path is a directory
        if is_directory is not None:
            if is_directory and not _is_directory:
                continue

            if not is_directory and _is_directory:
                continue

        # check if file or directory exsits
        if exists is not None:
            _exists = unsafe_abs_path.exists()

            if exists and not _exists:
                continue

            if not exists and _exists:
                continue

        # file found
        return str(unsafe_abs_path)

    raise FileNotFoundError(unsafe_path)

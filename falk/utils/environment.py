import os


def get_string(name, default):
    if name not in os.environ:
        value = default

        if callable(value):
            value = value()

        return value

    return os.environ["name"]


def get_boolean(name, default):
    if name not in os.environ:
        return default

    value = os.environ.get(name)

    return value.lower().strip() in ("1", "true", "yes", "on")


def get_integer(name, default):
    if name not in os.environ:
        return default

    return int(os.environ.get(name))

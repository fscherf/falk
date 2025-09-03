from importlib import import_module


def import_by_string(import_string):
    try:
        module_name, attribute_name = import_string.rsplit(".", 1)
        module = import_module(module_name)

        return getattr(module, attribute_name)

    except Exception as exception:
        raise ImportError(f"could not import {import_string}")

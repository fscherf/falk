def get_import_string(attribute):
    return f"{attribute.__module__}.{attribute.__qualname__}"

import hashlib

from falk.errors import UnknownComponentIdError, InvalidComponentError


def get_component_id(component, mutable_app):
    salt = mutable_app["settings"].get("component_id_salt", "")
    import_string = f"{component.__module__}.{component.__qualname__}"
    md5_hash = hashlib.md5()

    md5_hash.update(import_string.encode())
    md5_hash.update(salt.encode())

    return md5_hash.hexdigest()


def cache_component(component, mutable_app):
    # check if component is already cached
    if component in mutable_app["component_cache"]:
        return mutable_app["component_cache"][component]

    # check component
    if not callable(component):
        raise InvalidComponentError(
            f"components need to be callable. got {type(component)}",
        )

    # cache component
    component_id = mutable_app["settings"]["get_component_id"](
        component=component,
        mutable_app=mutable_app,
    )

    mutable_app["component_cache"].update({
        component_id: component,
        component: component_id,
    })

    return component_id


def get_component(component_id, mutable_app):
    try:
        return mutable_app["component_cache"][component_id]

    except KeyError as exception:
        raise UnknownComponentIdError() from exception

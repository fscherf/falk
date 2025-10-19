import hashlib

from falk.dependency_injection import get_dependencies
from falk.utils.iterables import add_unique_value
from falk.errors import UnknownComponentIdError
from falk.utils.path import get_abs_path


def get_component_id(component, mutable_app):
    if component in mutable_app["components"]:
        return mutable_app["components"][component]

    salt = mutable_app["settings"].get("component_id_salt", "")
    import_string = f"{component.__module__}.{component.__qualname__}"
    md5_hash = hashlib.md5()

    md5_hash.update(import_string.encode())
    md5_hash.update(salt.encode())

    return md5_hash.hexdigest()


def register_component(component, mutable_app):
    component_id = mutable_app["settings"]["get_component_id"](
        component=component,
        mutable_app=mutable_app,
    )

    if component not in mutable_app["components"]:
        mutable_app["components"][component_id] = component
        mutable_app["components"][component] = component_id

    _, dependencies = get_dependencies(
        callback=component,
    )

    for name, dependency in dependencies.items():

        # static dirs
        if name == "static_dirs":
            for rel_path in dependency:
                abs_path = get_abs_path(
                    caller=component,
                    path=rel_path,
                    require_directory=True,
                )

                add_unique_value(
                    mutable_app["settings"]["static_dirs"],
                    abs_path,
                )

        # components
        elif callable(dependency):
            register_component(
                component=dependency,
                mutable_app=mutable_app,
            )


def get_component(component_id, mutable_app):
    try:
        return mutable_app["components"][component_id]

    except KeyError as exception:
        raise UnknownComponentIdError() from exception

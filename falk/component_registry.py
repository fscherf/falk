import hashlib
import base64
import hmac

from falk.dependency_injection import get_dependencies
from falk.utils.iterables import add_unique_value
from falk.import_strings import get_import_string
from falk.errors import UnknownComponentIdError
from falk.utils.path import get_abs_path


def get_component_id(component, mutable_app):
    if component in mutable_app["components"]:
        return mutable_app["components"][component]

    secret = mutable_app["settings"]["token_secret"]
    import_string = get_import_string(component)

    signature = hmac.new(
        key=secret.encode(),
        msg=import_string.encode(),
        digestmod=hashlib.sha256,
    )

    component_id = base64.urlsafe_b64encode(signature.digest()).decode()

    return component_id


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

        # file upload handler
        elif name == "handle_file_upload":
            mutable_app["file_upload_handler"][component_id] = dependency

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


def get_file_upload_handler(component_id, mutable_app):
    return mutable_app["file_upload_handler"].get(
        component_id,
        mutable_app["settings"]["default_file_upload_handler"],
    )

from falk.contrib.django.auth import require
from falk.components import HTML5Base


def AuthComponent(request, HTML5Base=HTML5Base):
    require(
        request,
        login="require_login" in request["query"],
        staff="require_staff" in request["query"],
        permissions=request["query"].get("require_permissions", []),
        groups=request["query"].get("require_groups", []),
    )

    return """
        <HTML5Base title="Django 5.2 Index">
            <h1>Django Auth</h1>
            <div>
                User:
                <span id="user">{{ request.user.username or "AnonymousUser" }}</span>
            </div>
        </HTML5Base>
    """  # NOQA

from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.models import Session
from django.conf import settings as django_settings

from falk.components import format_exception
from falk.errors import ForbiddenError
from falk.routing import encode_query


def DjangoUserMiddleware(mutable_request, get_request_cookie):
    session_key = get_request_cookie("sessionid")
    user = AnonymousUser()

    if session_key["value"]:
        try:
            session = Session.objects.get(session_key=session_key["value"])
            user_pk = session.get_decoded().get("_auth_user_id")
            user = User.objects.get(pk=user_pk)

        except (Session.DoesNotExist, User.DoesNotExist):
            pass

    mutable_request["user"] = user


def require(
        request,
        login=False,
        staff=False,
        permissions=None,
        groups=None,
):

    user = request["user"]

    # login
    if login and not user.is_authenticated:
        raise ForbiddenError(f"{user} is not logged in")

    # staff
    if staff and not user.is_staff:
        raise ForbiddenError(f"{user} is no staff user")

    # permissions
    if permissions:
        user_permissions = request["user"].user_permissions.filter(
            codename__in=permissions,
        ).distinct(
        ).values_list(
            "codename",
            flat=True,
        )

        missing_permissions = set(permissions) - set(user_permissions)

        if len(missing_permissions) > 0:
            missing_permissions_string = ", ".join(missing_permissions)

            raise ForbiddenError(
                f"{user} does not have permission(s): {missing_permissions_string}",  # NOQA
            )

    # groups
    if groups:
        user_groups = request["user"].groups.filter(
            name__in=groups,
        ).distinct(
        ).values_list(
            "name",
            flat=True,
        )

        missing_groups = set(groups) - set(user_groups)

        if len(missing_groups) > 0:
            missing_groups_string = ", ".join(missing_groups)

            raise ForbiddenError(
                f"{user} is not in group(s): {missing_groups_string}",
            )


def get_forbidden_component(base_component):
    def DjangoForbiddenComponent(
            request,
            settings,
            exception,
            context,
            set_response_redirect,
            BaseComponent=base_component,
    ):

        # Django login form redirect
        if (not request["user"].is_authenticated and
                not request["is_mutation_request"]):

            next_location = encode_query(
                url=request["path"],
                query=request["query"],
            )

            location = f"{django_settings.LOGIN_URL}?next={next_location}"

            set_response_redirect(location)

            return

        # HTML response
        if settings["debug"]:
            (
                short_exception_string,
                exception_string,
            ) = format_exception(exception)

            context.update({
                "short_exception_string": short_exception_string,
                "exception_string": exception_string,
            })

        if request["is_mutation_request"]:
            return """
                <div class="falk-error">
                    Error 403:
                    {% if settings.debug %}
                        {{ short_exception_string }}
                    {% else %}
                        Forbidden
                    {% endif %}
                </div>
            """

        return """
            <BaseComponent title="403 Forbidden">
                <h1>Error 403</h1>
                <div class="falk-error">
                    {% if settings.debug %}
                        <pre>{{ exception_string }}</pre>
                    {% else %}
                        <p>Forbidden</p>
                    {% endif %}
                </div>
            </BaseComponent>
        """

    return DjangoForbiddenComponent

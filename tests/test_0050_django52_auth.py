# TODO: These tests test a bit much. Add dedicated tests for redirects
# and cookies

import pytest


def _run_in_thread(callback):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(callback)

        return future.result()


def _wait_for_database():
    import time

    from django.contrib.auth.models import User

    def callback():
        start = time.monotonic()
        timeout = 5

        while True:
            if time.monotonic() - start > timeout:
                raise TimeoutError("database did not came up in time")

            try:
                if User.objects.count() > 0:
                    return

                time.sleep(0.25)

            except Exception:
                time.sleep(0.25)

    _run_in_thread(callback)


def _login(page, base_url, username):
    page.goto(base_url + "/admin/login")
    page.wait_for_selector("form#login-form")

    # fill out form
    page.fill("input#id_username", username)
    page.fill("input#id_password", username)
    page.click("input[type=submit]")

    # wait for django admin
    page.wait_for_selector("body.dashboard")

    # check username
    page.goto(base_url + "/auth")
    assert page.text_content("#user") == username


def _goto_index(page, base_url):
    page.goto(base_url)
    page.wait_for_selector("body#index")


def _get_error_message(page):
    text = page.text_content(".falk-error")

    return text.strip().splitlines()[-1]


@pytest.mark.only_browser("chromium")
def test_login_url_redirects(page, start_falk_app):
    from falk.routing import encode_query

    from django52_test_app.app import asgi_app

    _, base_url = start_falk_app(
        asgi_app=asgi_app,
    )

    _wait_for_database()

    auth_url = base_url + "/auth"

    page.goto(auth_url)
    page.wait_for_selector("h1:text('Django Auth')")

    # nobody should be logged in
    assert page.text_content("#user") == "AnonymousUser"

    # if the user is an AnonymousUser, all `falk.contrib.django.auth.require`
    # calls should result in a redirect to the login URL
    urls = [
        encode_query(auth_url, {"require_login": "1"}),
        encode_query(auth_url, {"require_staff": "1"}),
        encode_query(auth_url, {"require_permissions": ["perm1", "perm2"]}),
        encode_query(auth_url, {"require_groups": ["group1", "group2"]}),
    ]

    for url in urls:
        _goto_index(page, base_url)
        page.goto(url)
        page.wait_for_selector("form#login-form")


@pytest.mark.only_browser("chromium")
def test_require_login(page, start_falk_app):
    from falk.routing import encode_query

    from django52_test_app.app import asgi_app

    _, base_url = start_falk_app(
        asgi_app=asgi_app,
    )

    _wait_for_database()

    url = encode_query(base_url + "/auth", {"require_login": "1"})

    _login(
        page=page,
        base_url=base_url,
        username="admin",
    )

    _goto_index(page, base_url)

    page.goto(url)

    assert page.text_content("#user") == "admin"


@pytest.mark.only_browser("chromium")
def test_require_staff(page, start_falk_app):
    from falk.routing import encode_query

    from django52_test_app.app import asgi_app

    _, base_url = start_falk_app(
        asgi_app=asgi_app,
    )

    _wait_for_database()

    url = encode_query(base_url + "/auth", {"require_staff": "1"})

    _login(
        page=page,
        base_url=base_url,
        username="admin",
    )

    _goto_index(page, base_url)

    page.goto(url)

    assert page.text_content("#user") == "admin"


@pytest.mark.only_browser("chromium")
def test_require_permissions(page, start_falk_app):
    from falk.routing import encode_query

    from django52_test_app.app import asgi_app

    _, base_url = start_falk_app(
        asgi_app=asgi_app,
    )

    auth_url = base_url + "/auth"

    _wait_for_database()

    _login(
        page=page,
        base_url=base_url,
        username="admin",
    )

    # setup permissions
    def add_permissions_to_admin():
        from django.contrib.auth.models import Permission, User

        admin = User.objects.get(username="admin")
        permissions = Permission.objects.all()[:3]

        for permission in permissions:
            admin.user_permissions.add(permission)

        admin.save()

        return list(
            admin.user_permissions.values_list(
                "codename",
                flat=True,
            )
        )

    permission_codenames = _run_in_thread(add_permissions_to_admin)

    # admin has all three permissions now so we should not run into an error
    # if we require all of them
    url = encode_query(auth_url, {
        "require_permissions": permission_codenames,
    })

    _goto_index(page, base_url)
    page.goto(url)

    assert page.text_content("#user") == "admin"

    # remove permissions
    def remove_permissions_from_admin(permission_codenames):
        from django.contrib.auth.models import Permission, User

        admin = User.objects.get(username="admin")

        for permission_codename in permission_codenames:
            admin.user_permissions.remove(
                Permission.objects.get(codename=permission_codename),
            )

    _run_in_thread(
        lambda: remove_permissions_from_admin(permission_codenames[1:]),
    )

    # admin lacks now two of the permissions which should raise
    # a `ForbiddenError`
    url = encode_query(auth_url, {
        "require_permissions": permission_codenames,
    })

    _goto_index(page, base_url)
    page.goto(url)
    error_message = _get_error_message(page)

    assert "ForbiddenError: " in error_message
    assert "admin does not have permission(s)"
    assert permission_codenames[1] in error_message
    assert permission_codenames[2] in error_message


@pytest.mark.only_browser("chromium")
def test_require_groups(page, start_falk_app):
    from falk.routing import encode_query

    from django52_test_app.app import asgi_app

    _, base_url = start_falk_app(
        asgi_app=asgi_app,
    )

    auth_url = base_url + "/auth"

    _wait_for_database()

    _login(
        page=page,
        base_url=base_url,
        username="admin",
    )

    # setup groups
    def add_admin_to_groups():
        from django.contrib.auth.models import Group, User

        admin = User.objects.get(username="admin")

        for name in ("group-1", "group-2", "group-3"):
            admin.groups.add(
                Group.objects.create(name=name),
            )

        admin.save()

        return list(
            admin.groups.values_list(
                "name",
                flat=True,
            )
        )

    group_names = _run_in_thread(add_admin_to_groups)

    # admin is in all three groups now so we should not run into an error
    # if we require all of them
    url = encode_query(auth_url, {
        "require_groups": group_names,
    })

    _goto_index(page, base_url)
    page.goto(url)

    assert page.text_content("#user") == "admin"

    # remove admin from groups permissions
    def remove_admin_from_groups(group_names):
        from django.contrib.auth.models import Group, User

        admin = User.objects.get(username="admin")

        for group_name in group_names:
            admin.groups.remove(
                Group.objects.get(name=group_name),
            )

    _run_in_thread(
        lambda: remove_admin_from_groups(group_names[1:]),
    )

    # admin is now in only one of three groups which should raise
    # a `ForbiddenError`
    url = encode_query(auth_url, {
        "require_groups": group_names,
    })

    _goto_index(page, base_url)
    page.goto(url)
    error_message = _get_error_message(page)

    assert "ForbiddenError: " in error_message
    assert "admin is not in group(s):"
    assert group_names[1] in error_message
    assert group_names[2] in error_message

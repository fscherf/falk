import pytest


@pytest.mark.only_browser("chromium")
def test_forms(page, start_falk_app):
    from django52_test_app.app import asgi_app

    _, base_url = start_falk_app(
        asgi_app=asgi_app,
    )

    auth_url = base_url + "/forms"

    page.goto(auth_url)
    page.wait_for_selector("h1:text('Django Form')")

    # no value
    assert page.input_value("input#id_character_field") == ""

    page.wait_for_selector("#message:text('No value')")

    # invalid value
    # the invalid value should stay in the form
    page.fill("input#id_character_field", "foo1")
    page.click("input[type=submit]")

    assert page.wait_for_selector("#message:text('Invalid value')")
    assert page.input_value("input#id_character_field") == "foo1"

    # valid value
    # if the form is valid, the form should be cleared
    page.fill("input#id_character_field", "foo")
    page.click("input[type=submit]")

    assert page.wait_for_selector("#message:text('Value: foo')")
    assert page.input_value("input#id_character_field") == ""

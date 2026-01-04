def test_post_requests(page, start_falk_app):
    import json

    from test_app.app import configure_app

    _, base_url = start_falk_app(
        configure_app=configure_app,
    )

    url = base_url + "/request-handling/post-forms"

    def get_form_data():
        return json.loads(
            page.text_content("pre.filled"),
        )

    def get_values(page):
        return {
            "text_field": page.input_value("input[name=text_field]"),
            "number_field": page.input_value("input[name=number_field]"),

            "textarea_field":
                page.input_value("textarea[name=textarea_field]"),

            "select_field": page.input_value("select[name=select_field]"),
        }

    # run test
    # First run: values should be visible in page and the form should not
    # be cleared
    page.goto(url)
    page.wait_for_selector("h2:text('POST Forms')")
    page.wait_for_selector("pre.empty", state="attached")

    page.fill("input[name=text_field]", "foo")
    page.fill("input[name=number_field]", "10")
    page.fill("textarea[name=textarea_field]", "bar")
    page.select_option("select[name=select_field]", value="option-2")

    page.click("input[type=submit]")

    assert get_form_data() == {
        "text_field": "foo",
        "number_field": "10",
        "textarea_field": "bar",
        "select_field": "option-2",
    }

    assert get_values(page) == {
        "text_field": "foo",
        "number_field": "10",
        "textarea_field": "bar",
        "select_field": "option-2",
    }

    # Second run: when `Update Form` is enabled "foo" should be rewritten
    # to "oof"
    page.goto(url)
    page.wait_for_selector("h2:text('POST Forms')")
    page.wait_for_selector("pre.empty", state="attached")

    page.fill("input[name=text_field]", "foo")
    page.fill("textarea[name=textarea_field]", "bar")
    page.check("input[name=update_form]")

    page.click("input[type=submit]")

    assert get_form_data() == {
        "update_form": "on",
        "text_field": "foo",
        "number_field": "",
        "textarea_field": "bar",
        "select_field": "option-1",
    }

    assert get_values(page) == {
        "text_field": "oof",
        "number_field": "",
        "textarea_field": "bar",
        "select_field": "option-1",
    }

    # Third run: when `Clear Form` is enabled the form should come back clear
    # after submit
    page.goto(url)
    page.wait_for_selector("h2:text('POST Forms')")
    page.wait_for_selector("pre.empty", state="attached")

    page.fill("input[name=text_field]", "foo")
    page.fill("input[name=number_field]", "10")
    page.fill("textarea[name=textarea_field]", "bar")
    page.select_option("select[name=select_field]", value="option-2")

    page.check("input[name=clear_form]")

    page.click("input[type=submit]")

    assert get_form_data() == {
        "clear_form": "on",
        "text_field": "foo",
        "number_field": "10",
        "textarea_field": "bar",
        "select_field": "option-2",
    }

    assert get_values(page) == {
        "text_field": "",
        "number_field": "",
        "textarea_field": "",
        "select_field": "option-1",
    }

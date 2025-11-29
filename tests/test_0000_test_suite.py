def test_package():
    import falk  # NOQA


def test_playwright_browser(page):
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(
            temp_dir,
            "hello-world.html",
        )

        with open(path, "w+") as file_handle:
            file_handle.write(
                '<h1 id="hello-world">Hello World</h1>'
            )

        page.goto(f"file://{path}")

        assert page.inner_text("#hello-world") == "Hello World"

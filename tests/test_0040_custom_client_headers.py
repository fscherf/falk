def test_custom_client_headers(start_falk_app, page):
    """
    This test ensures that `falk.httpTransport.setHeader` works before falk
    is fully initialized and afterwards too.

    We define two views: `SetCustomHeaderOnBeforeInitView` and
    `SetCustomHeaderOnClickView`.
    `SetCustomHeaderOnBeforeInitView` uses `falk.on("beforeinit")` to set a
    custom header before any other event handler run.
    `ShowCustomHeaderComponent` rerenders automatically `oninitialrender` so
    we should see the header immediately.

    `SetCustomHeaderOnClickView` sets no header initially so we should see
    `[NONE]` on start. The header gets then set by entering a custom value
    into the input and pressing the button.
    """

    from falk.components import HTML5Base

    def SetCustomHeaderBaseComponent(HTML5Base=HTML5Base):
        return """
            <HTML5Base props="{{ props }}" />

            <script>
                falk.on("beforeinit", () => {
                    falk.httpTransport.setHeader(
                        "X-Custom-Header",
                        "custom value",
                    );
                });
            </script>
        """

    def SetCustomHeaderComponent():
        return """
            <div id="set-header">
                <input type="text">
                <button onclick="setHeaderCallback(this.parentElement);">
                    Set Header
                </button>
            </div>

            <script>
                function setHeaderCallback(component) {
                    falk.httpTransport.setHeader(
                        "X-Custom-Header",
                        component.querySelector("input").value,
                    );

                    falk.runCallback({
                        selector: "#show-custom-header",
                        callbackName: "render",
                    });
                }
            </script>
        """

    def ShowCustomHeaderComponent(context, get_request_header):
        context.update({
            "custom_header": get_request_header("x-custom-header", "[NONE]"),
        })

        return """
            <div
                id="show-custom-header"
                oninitialrender="{{ callback(render) }}">

                <div id="custom-header">{{ custom_header }}</div>
            </div>
        """

    def SetCustomHeaderOnBeforeInitView(
            ShowCustomHeaderComponent=ShowCustomHeaderComponent,
            SetCustomHeaderBaseComponent=SetCustomHeaderBaseComponent,
    ):

        return """
            <SetCustomHeaderBaseComponent>
                <ShowCustomHeaderComponent />
            </SetCustomHeaderBaseComponent>
        """

    def SetCustomHeaderOnClickView(
            HTML5Base=HTML5Base,
            ShowCustomHeaderComponent=ShowCustomHeaderComponent,
            SetCustomHeaderComponent=SetCustomHeaderComponent,
    ):

        return """
            <HTML5Base>
                <ShowCustomHeaderComponent/>
                <SetCustomHeaderComponent/>
            </HTML5Base>
        """

    def configure_app(mutable_app, add_route):
        mutable_app["settings"]["websockets"] = False
        mutable_app["settings"]["debug"] = True

        add_route(
            "/set-custom-header-on-before-init(/)",
            SetCustomHeaderOnBeforeInitView,
        )

        add_route(
            "/set-custom-header-on-click(/)",
            SetCustomHeaderOnClickView,
        )

    _, base_url = start_falk_app(
        configure_app=configure_app,
    )

    # onbeforeinit
    page.goto(base_url + "/set-custom-header-on-before-init/")
    page.wait_for_selector("#custom-header:text('custom value')")

    # onclick
    page.goto(base_url + "/set-custom-header-on-click/")
    page.wait_for_selector("#custom-header:text('[NONE]')")

    page.fill("input", "foo")
    page.click("button")
    page.wait_for_selector("#custom-header:text('foo')")

    page.fill("input", "bar")
    page.click("button")
    page.wait_for_selector("#custom-header:text('bar')")

from test_app.components.base import Base


def RenderEventTestComponent(props, state, initial_render):
    if initial_render:
        state["id"] = props.get("id", None)

    return """
        <div
          class="render-event-test-component"
          id="{{ state.id }}"
          oninitialrender="renderEventTestComponentOnInitialRender(event, this)"
          onrender="renderEventTestComponentOnRender(event, this)">

            <span>#{{ state.id }}:</span>
            <span class="events"></span>

            <button class="render" onclick="{{ callback(render) }}">
                Render
            </button>
        </div>

        <script>
            function renderEventTestComponentOnInitialRender(event, node) {
                const span = node.querySelector("span.events");

                span.innerHTML = "initialRender";
            }

            function renderEventTestComponentOnRender(event, node) {
                const span = node.querySelector("span.events");

                    if (span.innerHTML) {
                        span.innerHTML += ",";
                    }

                span.innerHTML += "render";
            }
        </script>
    """


def RenderEvents(
        Base=Base,
        RenderEventTestComponent=RenderEventTestComponent,
):

    return """
        <Base title="Render Events">
            <h2>Render Events</h2>

            <RenderEventTestComponent id="component-1" />
            <RenderEventTestComponent id="component-2" />
            <RenderEventTestComponent id="component-3" />
        </Base>
    """

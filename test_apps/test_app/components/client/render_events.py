from test_app.components.base import Base


def RenderEventTestComponent(props, state, initial_render, template_context):
    if initial_render:
        state.update({
            "id": props.get("id", None),
            "unmount_callback": props.get("unmount_callback", ""),
        })

    return """
        <span
          onbeforerequest="renderEventTestComponentOnBeforeRequest(event, this)"
          onresponse="renderEventTestComponentOnResponse(event, this)"
          oninitialrender="renderEventTestComponentOnInitialRender(event, this)"
          onrender="renderEventTestComponentOnRender(event, this)"
          onbeforeunmount="renderEventTestComponentOnBeforeUnmount(event, this)">

            <button class="render" onclick="{{ falk.run_callback(render) }}">
                Render
            </button>

            <button class="unmount" onclick="{{ state.unmount_callback }}">
                Unmount
            </button>
        </span>

        <script>
            function renderEventTestComponentOnBeforeRequest(event, node) {
                const span = node.parentElement.querySelector("span.events");

                if (span.innerHTML) {
                    span.innerHTML += ",";
                }

                span.innerHTML += "beforeRequest";
            }

            function renderEventTestComponentOnResponse(event, node) {
                const span = node.parentElement.querySelector("span.events");

                if (span.innerHTML) {
                    span.innerHTML += ",";
                }

                span.innerHTML += "response";
            }

            function renderEventTestComponentOnInitialRender(event, node) {
                const span = node.parentElement.querySelector("span.events");

                if (span.innerHTML) {
                    span.innerHTML += ",";
                }

                span.innerHTML += "initialRender";
            }

            function renderEventTestComponentOnRender(event, node) {
                const span = node.parentElement.querySelector("span.events");

                if (span.innerHTML) {
                    span.innerHTML += ",";
                }

                span.innerHTML += "render";
            }

            function renderEventTestComponentOnBeforeUnmount(event, node) {
                const span = node.parentElement.querySelector("span.events");

                if (span.innerHTML) {
                    span.innerHTML += ",";
                }

                span.innerHTML += "unmount";
            }
        </script>
    """  # NOQA


def UnmountTestComponent():
    return """
        <div
          id="{{ props.id }}"
          onbeforeunmount="logUnmount(this)"
          style="padding-left: 2em">

            <span>#{{ props.id }}</span>
            {{ props.children }}
        </div>

        <script>
            function logUnmount(rootNode) {
                logElement = document.querySelector("#recursive-unmount-log");

                if (logElement.innerHTML) {
                    logElement.innerHTML += ",";
                }

                logElement.innerHTML += rootNode.id;
            }
        </script>
    """


def ReplaceTestComponent1():
    return """
        <div
          oninitialrender="replaceTestComponent1InitialRender(event)"
          onbeforeunmount="replaceTestComponent1Unmount(event)">

            <h3>Component 1</h3>
            <button
              id="replace-with-component-2"
              onclick="{{ props.onclick }}">

                Replace with Component 2
            </button>
        </div>

        <script>
            function replaceTestComponent1InitialRender(event) {
                const log = document.querySelector("pre#replace-log");

                log.innerHTML += "component 1: initialRender\\n";
            }

            function replaceTestComponent1Unmount(event) {
                const log = document.querySelector("pre#replace-log");

                log.innerHTML += "component 1: unmount\\n";
            }
        </script>
    """  # NOQA


def ReplaceTestComponent2():
    return """
        <div
          oninitialrender="replaceTestComponent2InitialRender(event)"
          onbeforeunmount="replaceTestComponent2Unmount(event)">

            <h3>Component 2</h3>
            <button
              id="replace-with-component-1"
              onclick="{{ props.onclick }}">

                Replace with Component 1
            </button>
        </div>

        <script>
            function replaceTestComponent2InitialRender(event) {
                const log = document.querySelector("pre#replace-log");

                log.innerHTML += "component 2: initialRender\\n";
            }

            function replaceTestComponent2Unmount(event) {
                const log = document.querySelector("pre#replace-log");

                log.innerHTML += "component 2: unmount\\n";
            }
        </script>
    """  # NOQA


def RenderEvents(
        initial_render,
        state,
        template_context,
        Base=Base,
        UnmountTestComponent=UnmountTestComponent,
        RenderEventTestComponent=RenderEventTestComponent,
        ReplaceTestComponent1=ReplaceTestComponent1,
        ReplaceTestComponent2=ReplaceTestComponent2,
):

    if initial_render:
        state.update({
            "render_components": [True, True, True, True],
            "show": 1,
        })

    def unmount(args):
        state["render_components"][args[0]] = False

    def replace(args):
        state["show"] = args[0]

    template_context.update({
        "unmount": unmount,
        "replace": replace,
    })

    return """
        <Base title="Render Events">
            <h2>Render Events</h2>

            <div id="component-1">
                <span>#component-1: </span>
                <span class="events" fx-preserve></span>

                {% if state.render_components[0] %}
                    <RenderEventTestComponent
                      id="component-1"
                      unmount_callback="{{ falk.run_callback(unmount, [0]) }}" />
                {% endif %}
            </div>

            <div id="component-2">
                <span>#component-2: </span>
                <span class="events" fx-preserve></span>

                {% if state.render_components[1] %}
                    <RenderEventTestComponent
                      id="component-2"
                      unmount_callback="{{ falk.run_callback(unmount, [1]) }}" />
                {% endif %}
            </div>

            <div id="component-3">
                <span>#component-3: </span>
                <span class="events" fx-preserve></span>

                {% if state.render_components[2] %}
                    <RenderEventTestComponent
                      id="component-3"
                      unmount_callback="{{ falk.run_callback(unmount, [2]) }}" />
                {% endif %}
            </div>

            <h2>Recursive unmount Events</h2>
            <div id="recursive-unmount-log" data-skip-rerender></div>

            <button
              id="recursive-unmount"
              onclick="{{ falk.run_callback(unmount, [3]) }}">
                Unmount
            </button>

            {% if state.render_components[3] %}
                <UnmountTestComponent id="unmount-test-component-1">
                    <UnmountTestComponent id="unmount-test-component-2">
                        <UnmountTestComponent id="unmount-test-component-3">
                        </UnmountTestComponent>
                    </UnmountTestComponent>
                </UnmountTestComponent>
            {% endif %}

            <h2>Replace Components</h2>
            <pre id="replace-log" fx-preserve></pre>

            {% if state.show == 1 %}
                <ReplaceTestComponent1 onclick="{{ falk.run_callback(replace, [2]) }}" />
            {% elif state.show == 2 %}
                <ReplaceTestComponent2 onclick="{{ falk.run_callback(replace, [1]) }}" />
            {% endif %}
        </Base>
    """  # NOQA

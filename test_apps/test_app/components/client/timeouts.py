import time

from test_app.components.base import Base


def TimeoutComponent(template_context, state, props, initial_render):
    if initial_render:
        state.update({
            "id": props.get("id", ""),
        })

    def slow_callback():
        time.sleep(5)

        template_context.update({
            "message": "rerender",
        })

    template_context.update({
        "slow_callback": slow_callback,
        "message": "initial render",
    })

    return """
        <div
          id="{{ state.id }}"
          onbeforerequest="setRequestTimeouts(event)"
          onresponse="clearRequestTimeouts(event)">

            <span>{{ state.id }}:</span>
            <span class="message">{{ message }}</span>
            <button onclick="{{ callback(slow_callback) }}">Rerender</button>
        </div>

        <script>
            const eventLogElement = document.querySelector("#event-log");
            const timeouts = new Map();

            function getTimeoutId(event) {
                return `${event.detail.nodeId}:${event.detail.requestId}`;
            }

            function setRequestTimeouts(event) {
                const rootNode = event.detail.rootNode;
                const messageElement = rootNode.querySelector(".message");

                messageElement.innerHTML = "waiting";

                const requestLateTimeout = setTimeout(() => {
                    messageElement.innerHTML = "response late";
                }, 3000);

                const requestTimeout = setTimeout(() => {
                    messageElement.innerHTML = "response timeout";
                }, 6000);

                timeouts.set(
                    getTimeoutId(event),
                    [requestLateTimeout, requestTimeout],
                );
            }

            function clearRequestTimeouts(event) {
                const timeoutId = getTimeoutId(event);
                const [requestLateTimeout, requestTimeout] = timeouts.get(timeoutId);

                clearTimeout(requestLateTimeout);
                clearTimeout(requestTimeout);

                timeouts.delete(timeoutId);
            }

            falk.on("beforerequest", (event) => {
                eventLogElement.innerHTML += `${event.detail.rootNode.id}: beforerequest\n`;
            });

            falk.on("response", (event) => {
                eventLogElement.innerHTML += `${event.detail.rootNode.id}: response\n`;
            });
        </script>
    """  # NOQA


def Timeouts(
        Base=Base,
        TimeoutComponent=TimeoutComponent,
):

    return """
        <Base title="Timeouts">
            <h2>Timeouts</h2>

            <TimeoutComponent id="timeout-component-1" />
            <TimeoutComponent id="timeout-component-2" />
            <TimeoutComponent id="timeout-component-3" />
            <TimeoutComponent id="timeout-component-4" />
            <TimeoutComponent id="timeout-component-5" />

            <h3>Event Log</h3>
            <pre id="event-log"></pre>
            <button id="clear-event-log">Clear</button>
        </Base>

        <script>
            document.querySelector(
                "#clear-event-log",
            ).addEventListener("click", () => {
                document.querySelector("#event-log").innerHTML = "";
            });
        </script>
    """

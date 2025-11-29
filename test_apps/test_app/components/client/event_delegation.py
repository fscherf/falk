import time

from test_app.components.base import Base


def EventDelegationTestComponent(props, state, initial_render, context):
    if initial_render:
        state["id"] = props.get("id", None)

    context.update({
        "slow_render": lambda: time.sleep(0.5),
    })

    return """
        <div class="event-delegation-test-component" id="{{ state.id }}">
            <span>#{{ state.id }}:</span>
            <span class="events"></span>

            <button class="render" onclick="{{ callback(slow_render) }}">
                Render
            </button>
        </div>

        <script>

            // falk.filterEvents (#component-1)
            document.addEventListener(
                "falk:beforerequest",
                falk.filterEvents(
                    ".event-delegation-test-component#component-1",
                    event => {
                        const span = event.target.querySelector("span.events");

                        if (span.innerHTML) {
                            span.innerHTML += ",";
                        }

                        span.innerHTML += "falk.filterEvents:beforeRequest";
                    },
                ),
            );

            document.addEventListener(
                "falk:initialrender",
                falk.filterEvents(
                    ".event-delegation-test-component#component-1",
                    event => {
                        const span = event.target.querySelector("span.events");

                        if (span.innerHTML) {
                            span.innerHTML += ",";
                        }

                        span.innerHTML += "falk.filterEvents:initialRender";
                    },
                ),
            );

            document.addEventListener(
                "falk:render",
                falk.filterEvents(
                    ".event-delegation-test-component#component-1",
                    event => {
                        const span = event.target.querySelector("span.events");

                        if (span.innerHTML) {
                            span.innerHTML += ",";
                        }

                        span.innerHTML += "falk.filterEvents:render";
                    },
                ),
            );

            // falk.on (#component-2)
            falk.on(
                "beforerequest",
                ".event-delegation-test-component#component-2",
                event => {
                    const span = event.target.querySelector("span.events");

                    if (span.innerHTML) {
                        span.innerHTML += ",";
                    }

                    span.innerHTML += "falk.on:beforeRequest";
                },
            );

            falk.on(
                "initialrender",
                ".event-delegation-test-component#component-2",
                event => {
                    const span = event.target.querySelector("span.events");

                    if (span.innerHTML) {
                        span.innerHTML += ",";
                    }

                    span.innerHTML += "falk.on:initialRender";
                },
            );

            falk.on(
                "render",
                ".event-delegation-test-component#component-2",
                event => {
                    const span = event.target.querySelector("span.events");

                    if (span.innerHTML) {
                        span.innerHTML += ",";
                    }

                    span.innerHTML += "falk.on:render";
                },
            );
        </script>
    """


def EventDelegation(
        Base=Base,
        EventDelegationTestComponent=EventDelegationTestComponent,
):

    return """
        <Base title="Event Delegation">
            <h2>Event Delegation</h2>

            <EventDelegationTestComponent id="component-1" />
            <EventDelegationTestComponent id="component-2" />
            <EventDelegationTestComponent id="component-3" />
        </Base>
    """

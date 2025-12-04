from test_app.components.base import Base


def Counter(props, state, context, initial_render):
    if initial_render:
        state.update({
            "id": props.get("id", ""),
            "initial_value": props.get("initial_value", 0),
            "count": props.get("initial_value", 0),
        })

    def update(args, event):
        operation, value = args

        if operation == "inc":
            state["count"] += value

        elif operation == "dec":
            state["count"] -= value

    def reset():
        state["count"] = state["initial_value"]

    context.update({
        "update": update,
        "reset": reset,
    })

    return """
        <div
          id="{{ state.id }}"
          class="client-side-counter"
          onInitialRender="clientSideCounterInit(this);">

            <button class="decrement">-</button>
            <span class="state">{{ state.count }}</span>
            <button class="increment">+</button>
            <button class="reset">Reset</button>
        </div>

        <script>
            function clientSideCounterInit(node) {
                const nodeSelector = `#${node.id}`;

                node.querySelector("button.increment").addEventListener("click", (event) => {
                    falk.runCallback({
                        node: node,
                        callbackName: "update",
                        callbackArgs: ["inc", 1],
                    });
                });

                node.querySelector("button.decrement").addEventListener("click", (event) => {
                    falk.runCallback({
                        selector: nodeSelector,
                        callbackName: "update",
                        callbackArgs: ["dec", 1],
                    });
                });

                node.querySelector("button.reset").addEventListener("click", (event) => {
                    falk.runCallback({
                        node: node,
                        callbackName: "reset",
                    });
                });
            }
        </script>
    """


def RunCallbackInJavascript(
        Base=Base,
        Counter=Counter,
):

    return """
        <Base title="runCallback in JavaScript">
            <h2>runCallback in JavaScript</h2>

            <Counter id="counter-1" initial_value="{{ 0 }}" />
            <Counter id="counter-2" initial_value="{{ 1 }}" />
            <Counter id="counter-3" initial_value="{{ 2 }}" />
            <Counter id="counter-4" initial_value="{{ 3 }}" />
            <Counter id="counter-5" initial_value="{{ 4 }}" />
        </Base>
    """

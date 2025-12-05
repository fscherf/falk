from test_app.components.base import Base


def Counter(props, state, context, initial_render, run_callback):
    if initial_render:
        state.update({
            "id": props.get("id", ""),
            "initial_value": props.get("initial_value", 0),
            "count": props.get("initial_value", 0),
        })

        run_callback(".counter", "update", ["inc", 1])

    def update(args, event):
        operation, value = args

        if operation == "inc":
            state["count"] += value

        elif operation == "dec":
            state["count"] -= value

    def reset():
        state["count"] = state["initial_value"]

    def _run_callback(args):
        selector, callback_name = args[0:2]
        _args = args[2:]

        run_callback(selector, callback_name, *_args)

    context.update({
        "update": update,
        "reset": reset,
        "_run_callback": _run_callback,
    })

    return """
        <div id="{{ state.id }}" class="counter">
            <button class="decrement" onclick="{{ callback(_run_callback, ['.counter', 'update', 'dec', 1]) }}">-</button>
            <span class="state">{{ state.count }}</span>
            <button class="increment" onclick="{{ callback(_run_callback, ['.counter', 'update', 'inc', 1]) }}">+</button>
            <button class="reset" onclick="{{ callback(_run_callback, ['.counter', 'reset']) }}">Reset</button>
        </div>
    """


def RunCallbackInPython(
        Base=Base,
        Counter=Counter,
):

    return """
        <Base title="run_callback In Python">
            <h2>run_callback in Python</h2>

            <Counter id="counter-1" initial_value="{{ 0 }}" />
            <Counter id="counter-2" initial_value="{{ 1 }}" />
            <Counter id="counter-3" initial_value="{{ 2 }}" />
            <Counter id="counter-4" initial_value="{{ 3 }}" />
            <Counter id="counter-5" initial_value="{{ 4 }}" />
        </Base>
    """

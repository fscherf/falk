from test_app.components.base import Base


def Counter(context, state, initial_render, props):
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
        <div class="counter" id="{{ state.id }}">
            <button
              class="decrement"
              onclick="{{ callback(update, ['dec', 1]) }}"
              >-</button>

            <span class="state">{{ state.count }}</span>

            <button
              class="increment"
              onclick="{{ callback(update, ['inc', 1]) }}"
              >+</button>

            <button
              class="reset"
              onclick="{{ callback(reset) }}"
              >Reset</button>
        </div>
    """


def Click(Base=Base, Counter=Counter):
    return """
        <Base title="Click Events">
            <h2>Click Events</h2>
            {% for i in range(5) %}
                <Counter
                  id="{{ 'counter-' + str(i) }}"
                  initial_value="{{ i }}" />
            {% endfor %}
        </Base>
    """

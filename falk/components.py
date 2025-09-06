def HTML5Base(props):
    return """
      <!DOCTYPE html>
      <html lang="{{ props.get("lang", "en") }}">
        <head>
          <meta charset="{{ props.get("charset", "UTF-8") }}">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <meta http-equiv="X-UA-Compatible" content="ie=edge">
          <title>{{ props.get("title", "") }}</title>
        </head>
        <body>
          {{ props.children }}
          {{ falk_scripts() }}
        </body>
      </html>
    """


def Counter(context, state, initial_render, props):
    if initial_render:
        state.update({
            "count": props.get("initial_value", 0),
        })

    def decrement():
        state["count"] -= 1

    def increment():
        state["count"] += 1

    context.update({
        "decrement": decrement,
        "increment": increment,
    })

    return """
        <div>
            <button onclick="{{ callback(decrement) }}">-</button>
            <span>{{ state.count }}</span>
            <button onclick="{{ callback(increment) }}">+</button>
        </div>
    """


def ItWorks(context):
    context.update({
        "HTML5Base": HTML5Base,
        "Counter": Counter,
    })

    return """
      <HTML5Base title="It works!">
        <h1>It works!</h1>
        <h2>Counter</h2>
        {% for i in range(5) %}
            <Counter initial_value="{{ i }}" />
        {% endfor %}
      </HTML5Base>
    """


def Error404(context, set_response_status):
    set_response_status(404)

    context.update({
        "HTML5Base": HTML5Base,
    })

    return """
        <HTML5Base title="404 Not Found">
            <h1>Error 404</h1>
            <p>Not Found</p>
        </HTML5Base>
    """

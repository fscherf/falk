def HTML5Base(props):
    return """
      <!DOCTYPE html>
      <html lang="{{ props.get('lang', 'en') }}">
        <head>
          <meta charset="{{ props.get('charset', 'UTF-8') }}">
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


def ItWorks(context):
    context.update({
        "HTML5Base": HTML5Base,
    })

    return """
      <HTML5Base title="It works!">
        <h1>It works!</h1>
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


def Error500(context, set_response_status, props):
    if not props["mutation_request"]:
        set_response_status(500)

    context.update({
        "HTML5Base": HTML5Base,
    })

    return """
        {% if props.mutation_request %}
            <div>Error 500: Internal Error</div>
        {% else %}
            <HTML5Base title="404 Not Found">
                <h1>Error 500</h1>
                <p>Internal Error</p>
            </HTML5Base>
        {% endif %}
    """

def HTML5Base(props):
    return """
      <!DOCTYPE html>
      <html lang="{{ props.get('lang', 'en') }}">
        <head>
          <meta charset="{{ props.get('charset', 'UTF-8') }}">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <meta http-equiv="X-UA-Compatible" content="ie=edge">
          <title>{{ props.get("title", "") }}</title>
          {{ falk_styles() }}
        </head>
        <body>
          {{ props.children }}
          {{ falk_scripts() }}
        </body>
      </html>
    """


def ItWorks(HTML5Base=HTML5Base):
    return """
      <HTML5Base title="It works!">
        <h1>It works!</h1>
      </HTML5Base>
    """


def Error404(set_response_status, HTML5Base=HTML5Base):
    set_response_status(404)

    return """
        <HTML5Base title="404 Not Found">
            <h1>Error 404</h1>
            <p>Not Found</p>
        </HTML5Base>
    """


def Error500(
        request,
        response,
        set_response_status,
        HTML5Base=HTML5Base,
):

    # reset response
    response.update({
        "is_finished": False,
        "content_type": "text/html",
        "body": None,
        "file_path": "",
        "json": None,
    })

    if not request["is_mutation_request"]:
        set_response_status(500)

    if request["is_mutation_request"]:
        return """
            <div>Error 500: Internal Error</div>
        """

    return """
        <HTML5Base title="500 Internal Error">
            <h1>Error 500</h1>
            <p>Internal Error</p>
        </HTML5Base>
    """

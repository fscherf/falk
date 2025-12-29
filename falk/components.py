import traceback
import html


def format_exception(exception):
    lines = traceback.format_exception(exception)

    return (
        html.escape(lines[-1]),
        html.escape("".join(lines)),
    )


def HTML5Base(props, context):
    html_attribute_string = ""
    body_attribute_string = ""

    for key, value in props.items():
        if key.startswith("html_"):
            html_attribute_string += (
                f'{key[5:]}="{value}" '
            )

        elif key.startswith("body_"):
            body_attribute_string += (
                f'{key[5:]}="{value}" '
            )

    context.update({
        "html_attribute_string": html_attribute_string,
        "body_attribute_string": body_attribute_string,
    })

    return """
      <!DOCTYPE html>
      <html
          lang="{{ props.get('lang', 'en') }}"
          _="{{ html_attribute_string }}">

        <head>
          <meta charset="{{ props.get('charset', 'UTF-8') }}">
          <meta http-equiv="X-UA-Compatible" content="ie=edge">

          <meta
            name="viewport" content="width=device-width, initial-scale=1.0">

          <title>{{ props.get("title", "") }}</title>
          {{ falk_styles() }}
        </head>
        <body _="{{ body_attribute_string }}">
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


def Error400(
        request,
        response,
        settings,
        exception,
        context,
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
        set_response_status(400)

    if settings["debug"]:
        short_exception_string, exception_string = format_exception(exception)

        context.update({
            "short_exception_string": short_exception_string,
            "exception_string": exception_string,
        })

    if request["is_mutation_request"]:
        return """
            <div class="falk-error">
                Error 400:
                {% if settings.debug %}
                    {{ short_exception_string }}
                {% else %}
                    Invalid Request
                {% endif %}
            </div>
        """

    return """
        <HTML5Base title="400 Invalid Request">
            <h1>Error 500</h1>
            <div class="falk-error">
                {% if settings.debug %}
                    <pre>{{ exception_string }}</pre>
                {% else %}
                    <p>Invalid Request</p>
                {% endif %}
            </div>
        </HTML5Base>
    """


def Error404(set_response_status, HTML5Base=HTML5Base):
    set_response_status(404)

    return """
        <HTML5Base title="404 Not Found">
            <h1>Error 404</h1>
            <div class="falk-error">
                <p>Not Found</p>
            </div>
        </HTML5Base>
    """


def Error500(
        request,
        response,
        settings,
        exception,
        context,
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

    if settings["debug"]:
        short_exception_string, exception_string = format_exception(exception)

        context.update({
            "short_exception_string": short_exception_string,
            "exception_string": exception_string,
        })

    if request["is_mutation_request"]:
        return """
            <div class="falk-error">
                Error 500:
                {% if settings.debug %}
                    {{ short_exception_string }}
                {% else %}
                    Internal Error
                {% endif %}
            </div>
        """

    return """
        <HTML5Base title="500 Internal Error">
            <h1>Error 500</h1>
            <div class="falk-error">
                {% if settings.debug %}
                    <pre>{{ exception_string }}</pre>
                {% else %}
                    <p>Internal Error</p>
                {% endif %}
            </div>
        </HTML5Base>
    """

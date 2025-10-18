from falk.components import HTML5Base


def Base(context, props):
    context.update({
        "HTML5Base": HTML5Base,
    })

    return """
        <link href="/static/base.css">

        <HTML5Base props="{{ props }}">
            {% if props.get("menu", True) %}
                <h1><a href="{{ get_url('index') }}">falk Test App</a></h1>
                <ul class="menu">
                    <li>
                        Rendering
                        <ul>
                            <li><a href="{{ get_url('rendering__styles_and_scripts') }}">Styles and Scripts</a></li>
                            <li><a href="{{ get_url('rendering__code_splitting') }}">Code Splitting</a></li>
                            <li><a href="{{ get_url('rendering__iframes') }}">iFrames</a></li>
                        </ul>
                    </li>
                    <li>
                        Events
                        <ul>
                            <li><a href="{{ get_url('events__render') }}">Render</a></li>
                            <li><a href="{{ get_url('events__click') }}">Click</a></li>
                            <li><a href="{{ get_url('events__input') }}">Input</a></li>
                            <li><a href="{{ get_url('events__change') }}">Change</a></li>
                            <li><a href="{{ get_url('events__submit') }}">Submit</a></li>
                        </ul>
                    </li>
                </ul>
                <hr />
            {% endif %}
            {{ props.children }}
        </HTML5Base>
    """

# Components

FIXME: basics, comparisino with jsx, self resolving dependencies


## Life Cycle

Whenever a component gets rendered or re rendered, the function body runs
**always**. You can check whether this is the first render or a rerender by
checking the dependency `initial_render`.

```python
def ClickableButton(props, initial_render, state, template_context):
    if initial_render:
        # This code only runs once when the component is rendered
        # initially, so we do all initiation steps here.

        state.update({
            "count": props.get("initial_value", 0),
        })

    def increase():
        # This code runs when the button is clicked, after the component
        # function already ran
        state["count"] += 1

    # This code runs on every render
    # 
    # Register the `increase` callback in the template context so it can be
    # used in `falk.run_callback`.
    template_context.update({
        "increase": increase,
    })

    return """
        <div class="counter">
            The current count is: <strong>{{ state.count }}</strong>!

            <button onclick="{{ falk.run_callback('increase') }}" >
                Increase
            </button>
        </div>
    """

```


FIXME: initial_render, render,


## Callbacks

FIXME: callbacks, callback args, callback passing

FIXME: callback events -> form_data


## Templating

Components are expected to return an HTML template as a string. This template
can contain multiple style blocks, multiple script blocks, and has to contain
one HTML block with exactly one root node.

The HTML block can contain either a full HTML document or just one
HTML element.

```python
def BaseComponent():
    # This component renders a whole HTML document

    return """
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <meta http-equiv="X-UA-Compatible" content="ie=edge">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">

          <!-- title given in props -->
          <title>{{ props.title }}</title>

          <!-- load styles -->
          {{ falk.get_styles() }}

        </head>
        <body>

          <!-- render child components -->
          {{ props.children }}

          <!-- load scripts -->
          {{ falk.get_scripts() }}

        </body>
      </html>
    """


def ClickableButton():
    # This component renders a clickable button with red text

    return """
        <style>
            button.clickable {
                color: red;
            }
        </style>

        <button class="clickable">Click Me!</button>
    """
```

Even to components which return entire HTML documments, you can still attach
script and style blocks. Falk will resolve all dependencies and template them
where `{{ falk.get_styles() }}` and `{{ falk.get_scripts() }}` were used.

```python
def ClickableButtonView(
        BaseComponent=BaseComponent,
        ClickableButton=ClickableButton,
):

    return """
        <BaseComponent title="Clickable Button">
            <ClickableButton />
        </BaseComponent>

        <script>
            window.onload = () => {
                console.log("Hello World");
            };
        </script>
    """
```



Falk parses component templates using an HTML parser. So even if Jinja2 syntax
is used, the component template has to be a valid HTML document.


!!! Success

    This works!

    Templating syntax is inside an element and in an element attribute.

    ```python
    def MyComponent():
        return """
            <button class="{% if 'clickable' in props %}clickable{% endif %}">
                {% if props.clickable %}
                    Click Me!
                {% endif %}
            </button>
        """
    ```

!!! danger

    This does not work!

    Templating syntax is outside the root element and inside the element
    instead of the elements attribute.

    ```python
    def MyComponent():
        return """
            {% if props.clickable %}
                <button {% if 'clickable' in props %}class="clickable"{% endif %}>
                    Click Me
                </button>
            {% endif%
        """
    ```

### Dynamic Attributes

If you want to dynamically generate attributes for an element you can use the
underscore attribute.

If falk encounters an attribute named `_` it will attach everything that was
templated in this attribute while rendering.

```python
def MyComponent():
    # This component will render to
    #
    #   <div foo="foo" bar="bar" baz="baz"></div>

    return """
        <div _='{% for i in ("foo", "bar", "baz") %}{{ i }}="{{ i }}"{% endfor %}'></div>
    """
```

### Trees

Components can call other components by using them as HTML elements. Attributes
are passed in as dict called `props`. The props are available in the template
as an dependency in the component function itself.

!!! note

    `props` are imutable by default. If you want to modify the props in your
    component function, you can use `mutable_props` instead.

If another component or a view wants to use a component, it has to define a
dependency as a function argument. Falk resolves these dependencies when
the component gets rendered.

```python
def ClickableButtonView(
        BaseComponent=BaseComponent,
        ClickableButton=ClickableButton,
):

    # This view renders a ClickableButton component inside a BaseComponent

    return """
        <BaseComponent title="Clickable Button">
            <ClickableButton />
        </BaseComponent>
    """
```

If a component renders HTML inside another component, the HTML is passed
to the component as `props.children` (see HTML document example from above).


### Props

By default, everything that is passed to a component is handled as a string:

```python
def MyComponent():
    # This will pass `foo` as a string to `OtherComponent`

    return """
       <OtherComponent foo="foo" /> 
    """
```

If you want to pass a data structure or an object you can use a
Jinja2 expression:

```python
def MyComponent():
    # This will pass `foo` as a boolean to `OtherComponent`

    return """
       <OtherComponent foo="{{ True }}" /> 
    """
```

## Render Modes

FIXME: children-skip, children-append, children-prepend


## Static Files

FIXME: static dirs as dependencies

FIXME: inline styles and scripts, external styles and scripts

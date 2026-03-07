# falk

[![PyPI - Version](https://img.shields.io/pypi/v/falk)](https://pypi.org/project/falk)
[![PyPI - License](https://img.shields.io/pypi/l/falk)](https://github.com/fscherf/falk/blob/master/LICENSE.txt)

FIXME: small introduction


[Getting Started](./getting-started/index.md)

[Tutorial](./tutorial/setup/index.md)










Falk is a responsive server rendered UI framework that treats frontend
technologies as an opt-in rather than a requirement.
Because of its stateless server architecture, it scales effortlessly over
process, server, and region boundaries.


### Stateless Server

Falk components can hold abstract state like the amount of a counter or which
tab in a tabbed layout is selected, without storing any data on the server.

This makes falk apps incredibly easy to scale. One worker can handle the
initial render of a component and every subsequent click or re render can be
handled by another worker or even another server, without migrating any data
between the two.

To achieve this, falk components return HTML and the state object that was used
to produce the HTML. Falk then renders the HTML in the browser, and stores the
state-object as a token. When the user requests re render, for example in an
onclick event, the browser sends the token back to the server in a mutation
requests and gets back a new token and new snipped of HTML to replace the
old one.

To make this process safe, falk tokens contain the component id, which is a
HMAC signature of the import string of the component, the state object itself,
JSON serialized, and a HMAC signature containing a configurable secret that
never leaves the server, signing the integrity of the entire token.

Even though the component state is visible to the user, the signature on state
and component id ensures that it can't be tampered with and the user also can't
just send ones components state to another component.

Token encoding and decoding functions can be configured, so if you need to hide
this data from the user, you can use encrypted JWTs for example.


### Minimal Mental Overhead

Falk does not define special data structures for state objects like apps,
routing tables, requests, or responses, etc. All data that falk holds and is
injected into components, middlewares, etc, consists of Python lists and dicts.

Falk also has next to no abstractions that hide what falk is doing under
the hood.
You don't have to read the documentation to figure out how to loop over all
HTTP headers in a request, you handle it like regular data in Python scripts.
You don't create an `EventRouterFactoryAdapterInterface` to setup an
onclick handler, You create your handler as a regular Python function and add
it to the template context which is a dictionary.

You might think that this is due to falk still having rough edges but this is
by design. Falk was born out of the frustration how much complexity and
mental load traditional UI frameworks burden their users with to do very
simple things.


### No forced Guardrails

Falk acknowledges that data that requires a specific format, like HTTP headers
or cookies, can become unsafe to handle if the user would be required to handle
the raw data all the time. Therefore, falk defines simple helpers like
`set_response_header()` or `get_request_cookie()` that you are allowed but
not forced to use.

For data structures like `request`, that should be read-only in most cases,
falk injects an immutable proxy so you can't change data accidentally. You can
still rewrite requests by using `mutable_request` instead.

Falk tries not to get in your way here but it wants you to be deliberate about
changing defaults.


### Everything is a function

Because the server is stateless and all UI state is stored on the client, falk
components are functions rather than classes. They don't hold state, they
produce and mutate state.

To keep the mental model and the API surface small, components, middlewares,
routes, file upload handler, etc, are all implemented as functions using
dependency injection.

This might seem unpythonic to you at first but it starts to make a lot of sense
once you scale up to multiple workers, servers, or regions even.


### Component Templates

Components have to return a component template which can contain multiple style
and script blocks and has to contain one HTML block with exactly one
root element.

Styles and scripts can be inlined or link to external files. Falk ensures that
all resources are completely loaded in the browser before the HTML gets
rendered.

```python
def MyComponent(template_context):
    template_context.update({
        "message": "foo bar baz",
    })

    return """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" >

        <style>
            span.word {
                color: red;
            }
        </style>

        <div class="my-component">
            {% for word in message.split(" ") %}
                <span class="word">{{ word }}</span>
            {% endfor %}
        </div>
    """
```

Only the HTML block can contain Jinja2 syntax. Style and script blocks can't.

Falk requires component templates to be valid but not complete HTML documents.
That means Jinja2 syntax is available within HTML tags and HTML attributes.
Nowhere else.

If you want to generate HTML attributes dynamically, you can use the underscore
attribute (`_`). Everything in there will be rendered without the underscore
in the browser.

```python
# valid
def MyComponent():
    return """
        <div class="{% if True %}my-component{% endif %}">
            My Component
        </div>
    """

def MyComponent():
    return """
        <div _='{% if True %}class="my-component"{% endif %}'>
            My Component
        </div>
    """

# invalid
def MyComponent():
    return """
        <div {% if True %}class="my-component"{% endif %}>
            My Component
        </div>
    """
```

### Static Files

### Component Composition

Components can use other components by defining them as a self resolving
dependency in their function signature. Only components defined as a dependency
are available in the component template.

The name can anything but it needs to start with an uppercase letter so falk
can distinguish components from regular HTML tags.

All attributes that you set on a component are passed into the component
function as `props`. If your component accepts child nodes, they are available
in `props.children`.

```python
def CenteredDiv(props, template_context):
    template_context.update({
        "class_string": props.get("class", ""),
    })

    return """
        <style>
            .centered {
                width: 50vw;
                margin: 0 auto;
            }
        </style>

        <div class="centered {{ class_string }}">
            {{ props.children }}
        </div>
    """


def MyComponent(
        CenteredDiv=CenteredDiv,  # define CenteredDiv as a dependency
):
    return """
        <CenteredDiv class="my-component">
            <h1>Hello World</h1>
        </CenteredDiv>
    """
```

Since components are stateless, `props` are only available on initial render.
When re rendering, `props` will be empty. All data that you need to be
persistent between renders needs to be copied into the `state` object.

```python
def Counter(props, state, initial_render):
    if initial_render:
        state.update({
            "initial_value": props.get("initial_value", 0),
        })

    return """
        <div class="counter">
            {{ state.initial_value }}
        </div>
    """
```

### Component Callbacks


### Component Life Cycle


### Moving State Between Components



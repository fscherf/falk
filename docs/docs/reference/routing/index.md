# Routing

Routes are configured by implementing a `configure_app` callback that
requires `add_route`.

```python
from falk.asgi import get_asgi_app
from falk.components import ItWorks

def configure_app(add_route):

    # static URL
    add_route("/it-works", ItWorks)

    # named route
    add_route("/it-works", ItWorks, name="it-works")

    # URL with optional trailing slash
    add_route("/it-works(/)", ItWorks)

    # URL with dynamic part
    # <article_id> will match any character but `/`
    add_route("/articles/<article_id>/edit", ItWorks)

    # regex URL
    add_route("/articles/<article_id:[a-z]+>/edit", ItWorks)

app = get_asgi_app(configure_app)
```

## Reverse Matching

You can generate a valid URL from a routes name by using the `get_url` callback
which can be required as a dependency.

```python
def MyComponent(get_url):
    url = get_url("it-works")
```

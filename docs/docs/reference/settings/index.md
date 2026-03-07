# Settings

You can configure a falk app by defining a `configure_app` callback, require
the `mutable_settings` state object, which is a simple Python dict, and update
its contents.

```python
from falk.asgi import get_asgi_app

def configure_app(mutable_settings):
    mutable_settings.update({
        "debug": True,
    })

app = get_asgi_app(configure_app)
```

## Core

### debug

**Type:** `bool`

**Default:** `False`

**Environment Variable:** `FALK_DEBUG`

If enabled, the default error components will show stacktraces in web.


### workers

**Type:** `int`

**Default:** `4`

**Environment Variable:** `FALK_WORKERS`

Max number of worker threads that get spawned.


### run_coroutine_sync

**Type:** `callable`

**Default:** `falk.asgi.get_asgi_app.app.run_coroutine_sync`

Callback that is used to run async dependencies, components, or
component callbacks.


## Middlewares

### pre_component_middlewares

**Type:** `List[callable]`

**Default:** `[]`

`pre_component_middlewares` are called before any components run.


### post_component_middlewares

**Type:** `List[callable]`

**Default:** `[]`

`post_component_middlewares` are called after all components run.


## Static Files

### static_url_prefix

**Type:** `str`

**Default:** `/static/`


### static_dirs

**Type:** `List[str]`

**Default:** `[falk.static_files.get_falk_static_dir()]`

List of directories that falk searches for static files in the order they
are listed.


## Templating

### extra_template_context

**Type:** `dict`

**Default:** `{}`

Gets passed into every templating context.


## Error Components

### bad_request_error_component

**Type:** `component`

**Default:** `falk.components.BadRequest`

Gets called whenever falk encounters an invalid request or an
`falk.errors.BadRequestError` is raised by a component or middleware.


### forbidden_error_component

**Type:** `component`

**Default:** `falk.components.Forbidden`

Gets called whenever an `falk.errors.ForbiddenError` is raised by a component
or middleware.


### not_found_error_component

**Type:** `component`

**Default:** `falk.components.NotFound`

Gets called whenever falk encounters an invalid URL or an
`falk.errors.NotFoundError` is raised by a component or middleware.


### internal_server_error_component

**Type:** `component`

**Default:** `falk.components.InternalServerError`

Gets called whenever falk encounters an unexpected error.


## Tokens

### token_secret

**Type:** `str`

**Default:** `falk.secrets.get_random_secret()`

**Environment Variable:** `FALK_TOKEN_SECRET`

Secret that gets used to for all HMAC signatures in tokens. This secret needs
to be shared between all workers so any worker can verify tokens issued by
other workers.


### encode_token

**Type:** `callable`

**Default:** `falk.tokens.encode_token`

**Signature:** `encode_token(component_id: str, data: Any, mutable_app: dict) -> str`

Gets called whenever falk needs to encode component state into a token.


### decode_token

**Type:** `callable`

**Signature:** `decode_token(token: str, mutable_app: dict) -> (component_id: str, component_state: Any)`

**Default:** `falk.tokens.decode_token`

Gets called whenever falk needs to decode a token from a mutation request.


## Components

### get_node_id

**Type:** `callable`

**Signature:** `get_node_id(mutable_app: dict) -> str`

**Default:** `falk.node_ids.get_node_id`

Gets called whenever falk needs to generate a node id. These are only used
for simple mappings on the client, so by default they are random.

The default callback uses `node_id_random_bytes` internally.


### node_id_random_bytes

**Type:** `int`

**Default:** `8`


## Component Registry

### get_component_id

**Type:** `callable`

**Default:** `falk.component_registry.get_component_id`


### register_component

**Type:** `callable`

**Default:** `falk.component_registry.register_component`


### get_component

**Type:** `callable`

**Default:** `falk.component_registry.get_component`


### get_file_upload_handler

**Type:** `callable`

**Default:** `falk.component_registry.get_file_upload_handler`

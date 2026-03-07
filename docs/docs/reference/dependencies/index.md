FIXME: custom dependencies

# Builtin Dependencies


## State Objects

### `request`

### `mutable_request`



## Components

| Type | Availability |
| - | - |
| callback | components |

```python
run_callback(
    callback_name: str,
    callback_args: list | dict,
    selector: str = "self",
    delay: float | int | str = 0,
) -> None

# Examples:
#
# Rerender the current component in 5 seconds.
#   run_callback('render', delay="5s")
#
# Run callback `tick` on all components with the class `clock`.
#   run_callback('tick', selector=".clock")
```


### `disable_state`

| Type | Availability |
| - | - |
| callback | components |

```python
disable_state() -> None
```


## Routing

### `get_url`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
get_url(
    route_name: str,
    route_args: Dict[str, Any],
    query: Dict[str, Any],
    checks: bool = True,
) -> str
```


## Static Files

### `get_static_url`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
get_static_url(
    rel_path: str,
) -> str
```


### `add_static_dir`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
get_static_url(
    rel_path: str,
) -> str
```


## Request Header

### `get_request_header`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
get_request_header(
    name: str,
    default: str | None = None,
) -> str
```


### `set_request_header`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
set_request_header(
    name: str,
    default: str,
) -> None
```


### `del_request_header`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
del_request_header(
    name: str,
) -> None
```


## Response Headers

### `get_response_header`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
get_response_header(
    name: str,
    default: str | None = None,
) -> str
```


### `set_response_header`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
set_response_header(
    name: str,
    default: str,
) -> None
```


### `del_response_header`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
del_response_header(
    name: str,
) -> None
```


## Request Cookies

### `get_request_cookie`

| Type | Availability |
| - | - |
| callback | middlewares, components, file upload handler |

```python
del_request_cookie(
    name: str,
) -> None
```

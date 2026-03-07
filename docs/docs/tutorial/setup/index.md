# Tutorial

## Setup

FIXME: we assume that you work in the same directory as the scripts

FIXME: we need a webserver -> uvicorn (optional), watchfiless for better DX

FIXME: uvicorn has support for websockets -> uvicorn[standard]

```
$ pip install falk
$ pip install uvicorn[standard] watchfiles
```

```python title="hello_world.py"
--8<-- "tutorial/setup/snippets/hello_world.py"
```

```
$ uvicorn --app-dir=./ hello_world:app
```

### Live Reload

FIXME: better DX

```
$ watchfiles "uvicorn --app-dir=./ hello_world:app" ./
```

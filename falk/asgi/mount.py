import os

from falk.errors import InvalidMountPointError


def Mount(asgi_app, lifespan=False, prefix=""):
    # TODO: add support for lifespans and make `lifespan` `True` by default

    if lifespan:
        raise NotImplementedError()

    if prefix and not prefix.startswith("/"):
        raise InvalidMountPointError("prefix needs to start with a slash")

    _prefix = prefix.lstrip("/")

    async def _asgi_app(
            mutable_app,
            asgi_scope,
            asgi_receive,
            asgi_send,
    ):

        _scope = asgi_scope.copy()

        if _prefix:

            # add prefix to root_path
            if "root_path" in _scope:
                _scope["root_path"] = os.path.join(
                    "/",
                    _scope["root_path"].lstrip("/"),
                    _prefix,
                )

            # remove prefix from path
            if "path" in _scope:
                _scope["path"] = os.path.join(
                    "/",
                    _scope["path"].lstrip("/")[len(_prefix):],
                )

        return await asgi_app(
            _scope,
            asgi_receive,
            asgi_send,
        )

    return _asgi_app

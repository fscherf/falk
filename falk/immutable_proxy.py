def get_immutable_proxy(data, name="", mutable_version_name=""):
    if isinstance(data, dict):
        return ImmutableProxyDict(
            data=data,
            name=name,
            mutable_version_name=mutable_version_name,
        )

    elif isinstance(data, list):
        return ImmutableProxyList(
            data=data,
            name=name,
            mutable_version_name=mutable_version_name,
        )

    return data


def _raise_error(proxy):
    error_message = "immutable data"

    if proxy._name:
        error_message = f"{proxy._name} is immutable"

        if proxy._mutable_version_name:
            error_message = f"{error_message}. use {proxy._mutable_version_name} instead"  # NOQA

    raise TypeError(error_message)


class ImmutableProxyDict(dict):
    def __init__(self, data, name="", mutable_version_name=""):
        self._data = data
        self._name = name
        self._mutable_version_name = mutable_version_name

    def __repr__(self):
        return f"<{self.__class__.__name__}({repr(self._data)})>"

    # proxied methods
    def __getitem__(self, key):
        return get_immutable_proxy(
            data=self._data.__getitem__(key),
            name=self._name,
            mutable_version_name=self._mutable_version_name,
        )

    def __iter__(self):
        for item in self._data:
            yield get_immutable_proxy(
                data=item,
                name=self._name,
                mutable_version_name=self._mutable_version_name,
            )

    def __contains__(self, *args, **kwargs):
        return self._data.__contains__(*args, **kwargs)

    def __bool__(self):
        return bool(self._data)

    def __len__(self):
        return self._data.__len__()

    def __eq__(self, *args, **kwargs):
        return self._data.__eq__(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self._data.get(*args, **kwargs)

    def items(self, *args, **kwargs):
        for key, value in self._data.items(*args, **kwargs):
            yield key, get_immutable_proxy(
                data=value,
                name=self._name,
                mutable_version_name=self._mutable_version_name,
            )

    def values(self, *args, **kwargs):
        for value in self._data.values(*args, **kwargs):
            yield get_immutable_proxy(
                data=value,
                name=self._name,
                mutable_version_name=self._mutable_version_name,
            )

    def keys(self, *args, **kwargs):
        return self._data.keys(*args, **kwargs)

    def reversed(self, *args, **kwargs):
        return self._data.reversed(*args, **kwargs)

    # blocked methods
    def __setitem__(self, *args, **kwargs):
        _raise_error(self)

    def __delitem__(self, *args, **kwargs):
        _raise_error(self)

    def clear(self, *args, **kwargs):
        _raise_error(self)

    def copy(self, *args, **kwargs):
        _raise_error(self)

    def pop(self, *args, **kwargs):
        _raise_error(self)

    def popitem(self, *args, **kwargs):
        _raise_error(self)

    def setdefault(self, *args, **kwargs):
        _raise_error(self)

    def update(self, *args, **kwargs):
        _raise_error(self)


class ImmutableProxyList(list):
    def __init__(self, data, name="", mutable_version_name=""):
        self._data = data
        self._name = name
        self._mutable_version_name = mutable_version_name

    def __repr__(self):
        return f"<{self.__class__.__name__}({repr(self._data)})>"

    # proxied methods
    def __getitem__(self, key):
        return get_immutable_proxy(
            data=self._data.__getitem__(key),
            name=self._name,
            mutable_version_name=self._mutable_version_name,
        )

    def __iter__(self):
        for item in self._data:
            yield get_immutable_proxy(
                data=item,
                name=self._name,
                mutable_version_name=self._mutable_version_name,
            )

    def __contains__(self, *args, **kwargs):
        return self._data.__contains__(*args, **kwargs)

    def __bool__(self):
        return bool(self._data)

    def __len__(self):
        return self._data.__len__()

    def __eq__(self, *args, **kwargs):
        return self._data.__eq__(*args, **kwargs)

    def index(self, *args, **kwargs):
        return self._data.index(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self._data.count(*args, **kwargs)

    # blocked methods
    def __setitem__(self, *args, **kwargs):
        _raise_error(self)

    def __delitem__(self, *args, **kwargs):
        _raise_error(self)

    def append(self, *args, **kwargs):
        _raise_error(self)

    def extend(self, *args, **kwargs):
        _raise_error(self)

    def insert(self, *args, **kwargs):
        _raise_error(self)

    def remove(self, *args, **kwargs):
        _raise_error(self)

    def pop(self, *args, **kwargs):
        _raise_error(self)

    def clear(self, *args, **kwargs):
        _raise_error(self)

    def sort(self, *args, **kwargs):
        _raise_error(self)

    def reverse(self, *args, **kwargs):
        _raise_error(self)

    def copy(self, *args, **kwargs):
        _raise_error(self)

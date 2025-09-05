def get_immutable_proxy(data):
    if isinstance(data, dict):
        return ImmutableProxyDict(data)

    elif isinstance(data, list):
        return ImmutableProxyList(data)

    return data


def _raise_error():
    raise TypeError("immutable data proxy")


class ImmutableProxyDict(dict):
    def __init__(self, data):
        self._data = data

    def __repr__(self):
        return f"<{self.__class__.__name__}({repr(self._data)})>"

    # proxied methods
    def __getitem__(self, key):
        return get_immutable_proxy(
            data=self._data.__getitem__(key)
        )

    def __iter__(self):
        for item in self._data:
            yield get_immutable_proxy(item)

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
            yield key, get_immutable_proxy(value)

    def values(self, *args, **kwargs):
        for value in self._data.values(*args, **kwargs):
            yield get_immutable_proxy(value)

    def keys(self, *args, **kwargs):
        return self._data.keys(*args, **kwargs)

    def reversed(self, *args, **kwargs):
        return self._data.reversed(*args, **kwargs)

    # blocked methods
    def __setitem__(self, *args, **kwargs):
        _raise_error()

    def __delitem__(self, *args, **kwargs):
        _raise_error()

    def clear(self, *args, **kwargs):
        _raise_error()

    def copy(self, *args, **kwargs):
        _raise_error()

    def pop(self, *args, **kwargs):
        _raise_error()

    def popitem(self, *args, **kwargs):
        _raise_error()

    def setdefault(self, *args, **kwargs):
        _raise_error()

    def update(self, *args, **kwargs):
        _raise_error()


class ImmutableProxyList(list):
    def __init__(self, data):
        self._data = data

    def __repr__(self):
        return f"<{self.__class__.__name__}({repr(self._data)})>"

    # proxied methods
    def __getitem__(self, key):
        return get_immutable_proxy(
            data=self._data.__getitem__(key)
        )

    def __iter__(self):
        for item in self._data:
            yield get_immutable_proxy(item)

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
        _raise_error()

    def __delitem__(self, *args, **kwargs):
        _raise_error()

    def append(self, *args, **kwargs):
        _raise_error()

    def extend(self, *args, **kwargs):
        _raise_error()

    def insert(self, *args, **kwargs):
        _raise_error()

    def remove(self, *args, **kwargs):
        _raise_error()

    def pop(self, *args, **kwargs):
        _raise_error()

    def clear(self, *args, **kwargs):
        _raise_error()

    def sort(self, *args, **kwargs):
        _raise_error()

    def reverse(self, *args, **kwargs):
        _raise_error()

    def copy(self, *args, **kwargs):
        _raise_error()

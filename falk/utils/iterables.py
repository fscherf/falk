def add_unique_value(iterable, value):
    if value in iterable:
        return

    iterable.append(value)


def extend_with_unique_values(iterable, values):
    for value in values:
        add_unique_value(iterable, value)

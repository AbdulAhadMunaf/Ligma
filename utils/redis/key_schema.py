DEFAULT_KEY_PREFIX = "backend"


def prefixed_key(func):
    """
    A method decorator that prefixes return values.

    Prefixes any string that the decorated method `f` returns with the value of
    the `prefix` attribute on the owner object `self`.
    """

    def prefixed_method(self, *args, **kwargs):
        key = func(self, *args, **kwargs)
        key = key.replace(" ", "")
        return f"{self.prefix}:{key}"

    return prefixed_method


class KeySchemaBase:
    """
    Methods to generate key names for Redis data structures.

    These key names are used by the DAO classes. This class therefore contains
    a reference to all possible key names used by this application.
    """

    def __init__(self, prefix: str = DEFAULT_KEY_PREFIX):
        self.prefix = prefix

    @prefixed_key
    def count_key(self, resource_name: str, query_params) -> str:
        # Exclude 'limit' and 'offset' keys
        query_params = {
            key: value
            for key, value in query_params.items()
            if key not in ("limit", "offset")
        }

        query_params = dict(sorted(query_params.items()))

        # Replace spaces with underscores in values and create a string in the format 'value1:value2'
        values = [value.replace(" ", "_") for value in query_params.values()]
        key = ":".join(values)
        return f"{resource_name}:count:{key}"

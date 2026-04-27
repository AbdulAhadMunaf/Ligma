import datetime

from django.db.models import Q


class FilterField(object):
    def __init__(self, lookup=None, cast=lambda x: x, operator="and", method_name=None):
        assert (
            lookup is not None or method_name is not None
        ), "lookup or method_name must be provided"
        self._lookup = lookup
        self._cast = cast
        self._operator: str = operator
        self._method_name: str = method_name

    def get_operator(self) -> str:
        return self._operator.lower()

    def get_method_name(self) -> str:
        return self._method_name

    def generate_filter(self, val, method=None):
        if method:
            return method(self._lookup, val)
        return {f"{self._lookup}": self._cast(val)}


class IntegerFilterField(FilterField):
    def __init__(self, *args, **kwargs):
        super(IntegerFilterField, self).__init__(*args, **kwargs)
        self._cast = lambda x: int(x)


class StringFilterField(FilterField):
    def __init__(self, *args, **kwargs):
        super(StringFilterField, self).__init__(*args, **kwargs)
        self._cast = lambda x: str(x)


class BooleanFilterField(FilterField):
    def __init__(self, *args, **kwargs):
        super(BooleanFilterField, self).__init__(*args, **kwargs)

    def generate_filter(self, val: str, method=None):
        val = val.lower() == "true"
        if method:
            return method(self._lookup, val)
        return {f"{self._lookup}": val}


class DateFilterField(FilterField):
    def __init__(self, *args, **kwargs):
        super(DateFilterField, self).__init__(*args, **kwargs)
        self._cast = lambda x: datetime.datetime.fromisoformat(x).date()


class DateTimeFilterField(FilterField):
    def __init__(self, *args, **kwargs):
        super(DateTimeFilterField, self).__init__(*args, **kwargs)
        self._cast = lambda x: datetime.datetime.fromisoformat(x)


class ListFilterField(FilterField):
    def __init__(self, dtype=str, *args, **kwargs):
        super(ListFilterField, self).__init__(*args, **kwargs)
        self.dtype = dtype
        self._cast = lambda x: list(map(self.dtype, x))

    def generate_filter(self, val: str, method=None):
        # Split the input string by commas and cast elements to the specified dtype
        val_list = self._cast(val.split(","))

        if method:
            return method(self._lookup, val_list)

        return {f"{self._lookup}": val_list}


class Filter(object):
    def __init__(self):
        self.fields = dict()
        for name, filter_field in self.__class__.__dict__.items():
            if isinstance(filter_field, FilterField):
                self.fields[name] = filter_field

    def get_clauses(self, **kwargs):
        clauses = Q()
        for name, value in kwargs.items():
            filter_field: FilterField = self.fields.get(name)
            if not filter_field:
                continue
            prepare = getattr(self, f"prepare_{name}", lambda x: x)
            value = prepare(value)
            method = None
            method_name = filter_field.get_method_name()
            if method_name:
                method = getattr(self, method_name, None)

            op = filter_field.get_operator()

            _filter = filter_field.generate_filter(value, method)

            _clause = _filter if isinstance(_filter, Q) else Q(**_filter)
            clauses &= _clause if op == "and" else _clause | clauses

        return clauses

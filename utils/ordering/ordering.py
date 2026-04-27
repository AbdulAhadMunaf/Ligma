class Ordering(object):
    sort_by_fields = {}

    @classmethod
    def get_order_field(cls, order_by, default):
        assert order_by and default, "order_by and default are required"

        # Check if order_by starts with a '-'
        is_descending = order_by.startswith("-")

        # Remove the '-' for lookup in the sort_by_fields dictionary
        clean_order_by = order_by[1:] if is_descending else order_by

        # Get the corresponding field from the sort_by_fields dictionary or use the default
        field = cls.sort_by_fields.get(clean_order_by)

        if field is None:
            return default

        # Reapply the '-' if the original order_by started with it
        return f"-{field}" if is_descending else field

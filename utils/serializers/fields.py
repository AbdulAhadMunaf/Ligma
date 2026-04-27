from rest_framework import serializers


class ChoicesDisplayField(serializers.Field):
    def to_representation(self, obj):
        model_field = self.parent.Meta.model._meta.get_field(self.field_name)
        if model_field.choices:
            choices_dict = dict(model_field.choices)
            return {"key": obj, "display_name": choices_dict.get(obj)}
        return obj


class JsonFriendlyDateField(serializers.DateField):
    def to_internal_value(self, data):
        return str(super().to_internal_value(data))

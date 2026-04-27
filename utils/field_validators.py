from django.core.exceptions import ValidationError


def validate_length(value, length=13):
    if len(str(value)) != length:
        raise ValidationError("%s is not the correct length" % value)

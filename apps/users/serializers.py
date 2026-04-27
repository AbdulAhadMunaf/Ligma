from rest_framework import serializers

from apps.users.models import User


def _validate_email(email):
    if User.objects.filter(email=email).exists():
        raise serializers.ValidationError("User Already Exist with this email")
    return email

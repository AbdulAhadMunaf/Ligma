from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import User


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError("The new passwords do not match.")
        user = self.context["user"]
        if not user.check_password(old_password):
            raise serializers.ValidationError("Wrong old password.")

        # Validate the new password using Django's password validation
        try:
            validate_password(new_password, user=user)
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return data


class UserRetrieveSerializer(serializers.ModelSerializer):

    groups = serializers.SerializerMethodField()

    def get_groups(self, instance):
        return instance.groups.all().values_list("name", flat=True)

    class Meta:
        model = User
        fields = (
            "id",
            "is_active",
            "name",
            "email",
            "pwd_reset_required",
            "groups",
            "permissions",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        groups = data.get("groups")

        if len(groups) > 0:
            groups[0]

        return data

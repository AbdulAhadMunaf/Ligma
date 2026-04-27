from utils.choices.choices import BaseChoices


class UserPermissionChoices(BaseChoices):

    CAN_CREATE_COMPANY_USER = "can_create_company_user", "Can create company user"
    CAN_ASSIGN_ROLE_TO_COMPANY_USER = (
        "can_assign_role_to_company_user",
        "Can assign role to company user",
    )


class UserGroupChoices(BaseChoices):

    SUPER_ADMIN = "super_admin", "super_admin"

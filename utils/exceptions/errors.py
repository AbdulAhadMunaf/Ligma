from enum import Enum


class BaseErrorEnum(Enum):
    def __init__(self, error):
        self.error_code = error[0]
        self.error_message = error[1]

    @property
    def code(self):
        return self.error_code

    @property
    def message(self):
        return self.error_message


class CoreError(BaseErrorEnum):
    SOMETHING_WENT_WRONG = (
        (1000, "Something went wrong. Please contact to Administrator"),
    )
    INVALID_CREDENTIALS = (
        (1001, "Invalid Credentials OR account has been blocked. Please try again"),
    )
    INVALID_TOKEN = ((1002, "Invalid Token"),)
    AUTH_TOKEN_EXPIRED = ((1003, "Auth Token has been Expired"),)
    BLOCKED_USER = ((1004, "User is blocked"),)
    CREDENTIALS_NOT_FOUND = ((1005, "Credentials not found"),)


class CoreResourceNotFoundError(BaseErrorEnum):
    RESOURCE_NOT_FOUND = ((2000, "Resource Not Found"),)
    RESOURCE_NOT_FOUND_CUSTOM_MSG = ((2005, "{value}"),)


class CoreValidationError(BaseErrorEnum):
    VALIDATION_ERROR = ((3000, "Validation Error"),)


class CoreAuthorizedError(BaseErrorEnum):
    UNAUTHORIZED_ERROR = ((4000, "User is not authorized to perform this action"),)
    PWD_RESET_REQUIRED = ((4001, "Please reset your password to continue."),)


class DatesError(BaseErrorEnum):
    BOTH_DATES_REQUIRED_ERROR = (
        (5000, "Please provide both start_date and end_date."),
    )
    START_DATE_BEFORE_END_DATE_ERROR = ((5001, "start_date must be before end_date."),)
    INVALID_DATE_FORMAT_ERROR = ((5001, "Invalid date format. Please use YYYY-MM-DD."),)


class QueryParamError(BaseErrorEnum):
    INVALID_QUERY_STRUCTURE_ERROR = ((6000, "Invalid query structure"),)
    TOP_QUERY_PARAM_REQUIRED_ERROR = ((6001, "Top query parameter is required"),)
    REQUIRED_QUERY_PARAM = ((6002, "{value}"),)


class PlannedRouteError(BaseErrorEnum):
    CANNOT_DELETE_PLANNED_ROUTE_STOCK_FULL = (
        (7000, "Cannot delete planned route, because stock is full"),
    )


class QuerySchedulerError(BaseErrorEnum):
    NAME_ALREADY_EXISTS = ((8000, "{value}"),)

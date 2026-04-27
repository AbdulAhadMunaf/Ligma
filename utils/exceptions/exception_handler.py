import traceback

from rest_framework.response import Response
from rest_framework.views import exception_handler

from utils.response.resp import APIResponse

from .errors import (
    CoreAuthorizedError,
    CoreError,
    CoreResourceNotFoundError,
    CoreValidationError,
)
from .exceptions import CoreBaseException, CoreValidationException


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    exception_class = exc.__class__.__name__
    handlers = {
        # Rest Framework Exceptions
        "ValidationError": _handle_validation_error,
        "Http404": _handle_not_found_error,
        "PermissionDenied": _handle_authenticated_error,
        "InvalidToken": _handle_invalid_token_error,
        "AuthenticationFailed": _handle_invalid_cred_error,
        "NotAuthenticated": _handle_cred_not_found_error,
        # Other Exceptions
        "TokenError": _handle_token_error,
        "KeyError": _handle_key_error,
        "DoesNotExist": _handle_resource_does_not_exist_error,
    }
    if isinstance(exc, CoreBaseException):
        return _handle_tom_base_exceptions(exc, context, response)
    if exception_class in handlers:
        return handlers[exception_class](exc, context, response)

    return _handle_unexpected_error(exc, context, response)


# Rest Exception Handlers


def _handle_unexpected_error(exc, context, response):
    traceback.print_exc()

    res = APIResponse.get_response(
        code=CoreError.SOMETHING_WENT_WRONG.code,
        message=CoreError.SOMETHING_WENT_WRONG.message,
    )
    if response is None:
        return Response(res, status=500)

    response.data = res
    return response


def _handle_not_found_error(exc, context, response):
    response.data = APIResponse.get_response(
        code=CoreResourceNotFoundError.RESOURCE_NOT_FOUND.code,
        message=CoreResourceNotFoundError.RESOURCE_NOT_FOUND.message,
    )
    return response


def _handle_authenticated_error(exc, context, response):
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        detail_code = exc.detail.get("code")
        exc.detail.get("message")

        # DRF wraps values in ErrorDetail objects, so extract the actual value
        if hasattr(detail_code, "__str__"):
            detail_code = int(str(detail_code))
        elif detail_code is not None:
            detail_code = int(detail_code)

        if detail_code == CoreAuthorizedError.PWD_RESET_REQUIRED.code:
            response.data = APIResponse.get_response(
                code=CoreAuthorizedError.PWD_RESET_REQUIRED.code,
                message=CoreAuthorizedError.PWD_RESET_REQUIRED.message,
            )
            return response

    response.data = APIResponse.get_response(
        code=CoreAuthorizedError.UNAUTHORIZED_ERROR.code,
        message=CoreAuthorizedError.UNAUTHORIZED_ERROR.message,
    )
    return response


def _handle_invalid_token_error(exc, context, response):
    response.data = APIResponse.get_response(
        code=CoreError.INVALID_TOKEN.code,
        message=CoreError.INVALID_TOKEN.message,
    )
    return response


def _handle_invalid_cred_error(exc, context, response):
    response.data = APIResponse.get_response(
        code=CoreError.INVALID_CREDENTIALS.code,
        message=CoreError.INVALID_CREDENTIALS.message,
    )
    return response


def _handle_cred_not_found_error(exc, context, response):
    response.data = APIResponse.get_response(
        code=CoreError.CREDENTIALS_NOT_FOUND.code,
        message=CoreError.CREDENTIALS_NOT_FOUND.message,
    )
    return response


def _handle_validation_error(exc, context, response):
    response.data = APIResponse.get_response(
        error=exc.detail,
        code=CoreValidationError.VALIDATION_ERROR.code,
        message=CoreValidationError.VALIDATION_ERROR.message,
    )
    return response


def _handle_tom_base_exceptions(exc, context, response):
    if isinstance(exc, CoreValidationException):
        response.data = APIResponse.get_response(
            error=exc.error,
            code=CoreValidationError.VALIDATION_ERROR.code,
            message=CoreValidationError.VALIDATION_ERROR.message,
        )
    else:
        response.data = APIResponse.get_response(
            code=exc.error.code,
            message=exc.error.message.format(value=exc.value),
        )
    return response


# Other Handlers


def _handle_token_error(exc, context, response):
    return Response(
        APIResponse.get_response(
            code=CoreError.INVALID_TOKEN.code,
            message=CoreError.INVALID_TOKEN.message,
        ),
        status=400,
    )


def _handle_resource_does_not_exist_error(exc, context, response):
    return Response(
        APIResponse.get_response(
            code=CoreResourceNotFoundError.RESOURCE_NOT_FOUND.code,
            message=CoreResourceNotFoundError.RESOURCE_NOT_FOUND.message,
        ),
        status=404,
    )


def _handle_key_error(exc, context, response):
    traceback.print_exc()
    return Response(
        APIResponse.get_response(
            code=CoreValidationError.VALIDATION_ERROR.code,
            message=CoreValidationError.VALIDATION_ERROR.message,
            error={exc.args[0]: [exc.args[0] + " is invalid"]},
        ),
        status=400,
    )

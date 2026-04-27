from contextlib import contextmanager

from rest_framework.exceptions import APIException


@contextmanager
def does_not_raise():
    yield


class CoreBaseException(APIException):
    pass


class CoreException(CoreBaseException):
    def __init__(self, error, value: str = ""):
        self.error = error
        self.value = value
        self.status_code = 400
        super().__init__(self.error, self.status_code)


class CoreValidationException(CoreBaseException):
    def __init__(self, error, value: str = ""):
        self.error = error
        self.value = value
        self.status_code = 400
        super().__init__(self.error, self.status_code)


class CoreResourceNotFoundException(CoreBaseException):
    def __init__(self, error, value: str = ""):
        self.error = error
        self.value = value
        self.status_code = 404
        super().__init__(self.error, self.status_code)


class CoreResourceAlreadyExistException(CoreBaseException):
    def __init__(self, error, value: str = ""):
        self.error = error
        self.value = value
        self.status_code = 409
        super().__init__(self.error, self.status_code)


class CoreUnuthenticatedException(CoreBaseException):
    def __init__(self, error, value: str = ""):
        self.error = error
        self.value = value
        self.status_code = 401
        super().__init__(self.error, self.status_code)


class CoreUnauthorizedException(CoreBaseException):
    def __init__(self, error, value: str = ""):
        self.error = error
        self.value = value
        self.status_code = 403
        super().__init__(self.error, self.status_code)

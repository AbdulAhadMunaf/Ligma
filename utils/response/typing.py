from mypy_extensions import TypedDict


class CoreApiResponse(TypedDict):
    message: str
    data: dict
    error: dict

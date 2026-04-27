from utils.response.typing import CoreApiResponse

""" # noqa
from rest_framework.response import Response

# 1 Response take get_response function
# 2 Status code by default is 200 and if you want to use other status codes than you can pass other status code as well

return Response(
                APIResponse.get_response(

                message="Any message",
                data={},
                error={},
                ),
                status_code
            )

"""


class APIResponse:
    @staticmethod
    def get_response(
        message: str = "",
        code: int = 0,
        data: dict = None,
        error: dict = None,
        pagination_data: dict = None,
    ) -> CoreApiResponse:
        data = {} if data is None else data
        error = {} if error is None else error
        pagination_data = {} if pagination_data is None else pagination_data
        return {
            "message": message,
            "code": code,
            "data": data,
            "error": error,
            **({"pagination": pagination_data} if pagination_data else {}),
        }

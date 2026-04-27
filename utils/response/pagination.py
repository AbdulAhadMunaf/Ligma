from rest_framework import mixins
from rest_framework.response import Response

from .resp import APIResponse


class CorePagination(mixins.ListModelMixin):
    def paginated_response(self, request):
        serializer = self.list(request)

        pagination_response = {
            "count": serializer.data["count"],
            "next": serializer.data["next"],
            "previous": serializer.data["previous"],
        }

        return Response(
            APIResponse.get_response(
                data=serializer.data["results"],
                is_paginated=True,
                pagination_data=pagination_response,
            )
        )

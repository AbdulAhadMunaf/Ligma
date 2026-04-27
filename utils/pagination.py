from django.core.cache import cache
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from utils.response.resp import APIResponse


class CorePagination(LimitOffsetPagination):
    default_limit = 50

    def paginate_queryset(self, queryset, request, view=None):
        self.key_schema_class = getattr(view, "key_schema_class", None)
        self.resource_name = getattr(view, "resource_name", None)

        self.count = self.get_count(request, queryset)

        limit = self.get_limit(request)
        offset = self.get_offset(request)
        if offset is not None and limit is not None:
            queryset = queryset[offset : offset + limit]
        return list(queryset)

    def get_paginated_response(self, data):
        pagination_response = {
            "count": self.count,
        }
        return Response(
            APIResponse.get_response(
                data=data,
                pagination_data=pagination_response,
            )
        )

    def get_count(self, request, queryset):  # Get all query parameters
        count = super().get_count(queryset)
        if self.key_schema_class and self.resource_name:
            key_schema = self.key_schema_class()
            count_key = key_schema.count_key(self.resource_name, request.query_params)
            return cache.get_or_set(count_key, count)

        return count

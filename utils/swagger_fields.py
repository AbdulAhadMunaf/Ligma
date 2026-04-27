from drf_yasg import openapi

q = openapi.Parameter(
    "q",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    required=False,
    description="Full text search",
)

sort_by = openapi.Parameter(
    "sort_by",
    openapi.IN_QUERY,
    type=openapi.TYPE_STRING,
    required=False,
)


object_id = openapi.Parameter(
    "object_id",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_INTEGER,
    required=False,
)

file_id = openapi.Parameter(
    "file_id",
    in_=openapi.IN_QUERY,
    type=openapi.TYPE_INTEGER,
    required=False,
)

file = openapi.Parameter(
    "file",
    openapi.IN_FORM,
    description="file of any type.",
    type=openapi.TYPE_FILE,
    required=True,
)

from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.settings.serializers import ChangePasswordSerializer, UserRetrieveSerializer
from utils.response.resp import APIResponse


class UserChangePasswordAPI(APIView):
    @swagger_auto_schema(
        tags=["settings"],
        request_body=ChangePasswordSerializer,
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        new_password = serializer.data.get("new_password")

        user.set_password(new_password)
        user.save()

        return Response(
            APIResponse.get_response(
                message="Password changed successfully",
            )
        )


class UserMeAPI(APIView):
    @swagger_auto_schema(tags=["settings"])
    def get(self, request):
        serializer = UserRetrieveSerializer(request.user)
        return Response(
            APIResponse.get_response(
                data=serializer.data,
            )
        )

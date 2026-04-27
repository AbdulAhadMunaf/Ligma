from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collaboration.api.serializers import (
    CollaborationNodeAccessSerializer,
    CollaborationNodeAccessUpsertSerializer,
    CollaborationProxyPublishSerializer,
    CollaborationRoomCreateSerializer,
    CollaborationRoomEventCreateSerializer,
    CollaborationRoomEventSerializer,
    CollaborationRoomMemberSerializer,
    CollaborationRoomMemberUpsertSerializer,
    CollaborationRoomSerializer,
)
from apps.collaboration.models import CollaborationRoom
from apps.collaboration.services.centrifugo_service import CentrifugoService
from apps.collaboration.services.room_service import CollaborationRoomService
from utils.response.resp import APIResponse

User = get_user_model()


class CollaborationRoomListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request):
        room_queryset = CollaborationRoomService.list_rooms_for_user(request.user)
        serializer = CollaborationRoomSerializer(room_queryset, many=True)
        return Response(APIResponse.get_response(data={"rooms": serializer.data}))

    @swagger_auto_schema(
        tags=["collaboration"],
        request_body=CollaborationRoomCreateSerializer,
    )
    def post(self, request):
        serializer = CollaborationRoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = CollaborationRoomService.create_room(
            creator=request.user,
            name=serializer.validated_data["name"],
            metadata=serializer.validated_data.get("metadata"),
        )
        room = (
            CollaborationRoom.objects.select_related("created_by")
            .prefetch_related("members__user", "members__group")
            .get(pk=room.pk)
        )
        response_serializer = CollaborationRoomSerializer(room)
        return Response(
            APIResponse.get_response(
                message="Collaboration room created successfully.",
                data=response_serializer.data,
            ),
            status=status.HTTP_201_CREATED,
        )


class CollaborationRoomDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        room = (
            CollaborationRoom.objects.select_related("created_by")
            .prefetch_related("members__user", "members__group")
            .get(pk=room.pk)
        )
        serializer = CollaborationRoomSerializer(room)
        return Response(APIResponse.get_response(data=serializer.data))


class CollaborationRoomMemberListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        serializer = CollaborationRoomMemberSerializer(room.members.all(), many=True)
        return Response(APIResponse.get_response(data={"members": serializer.data}))

    @swagger_auto_schema(
        tags=["collaboration"],
        request_body=CollaborationRoomMemberUpsertSerializer,
    )
    def post(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        serializer = CollaborationRoomMemberUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_user = User.objects.filter(id=serializer.validated_data["user_id"]).first()
        if not member_user:
            return Response(
                APIResponse.get_response(code=404, message="User not found."),
                status=status.HTTP_404_NOT_FOUND,
            )
        membership = CollaborationRoomService.upsert_member(
            room=room,
            actor=request.user,
            member_user=member_user,
            role=serializer.validated_data["role"],
        )
        response_serializer = CollaborationRoomMemberSerializer(membership)
        return Response(
            APIResponse.get_response(
                message="Room member saved successfully.",
                data=response_serializer.data,
            )
        )


class CollaborationRoomSceneAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        membership = CollaborationRoomService.assert_can_view(room=room, user=request.user)
        return Response(
            APIResponse.get_response(
                data={
                    "room_id": str(room.room_uuid),
                    "channel": room.channel_name,
                    "membership": CollaborationRoomMemberSerializer(membership).data,
                    "initial_data": CollaborationRoomService.build_initial_data(room),
                }
            )
        )


class CollaborationRoomNodeAccessListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        serializer = CollaborationNodeAccessSerializer(room.node_access_entries.all(), many=True)
        return Response(APIResponse.get_response(data={"node_access": serializer.data}))

    @swagger_auto_schema(
        tags=["collaboration"],
        request_body=CollaborationNodeAccessUpsertSerializer,
    )
    def post(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_manage_members(room=room, user=request.user)
        serializer = CollaborationNodeAccessUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        node_access, _ = room.node_access_entries.update_or_create(
            node_id=serializer.validated_data["node_id"],
            defaults={
                "allowed_roles": serializer.validated_data["allowed_roles"],
                "metadata": serializer.validated_data.get("metadata") or {},
                "locked_by": request.user,
            },
        )
        return Response(
            APIResponse.get_response(
                message="Node access saved successfully.",
                data=CollaborationNodeAccessSerializer(node_access).data,
            )
        )


class CollaborationRoomEventListCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        after_sequence = int(request.query_params.get("after_sequence", 0))
        limit = min(int(request.query_params.get("limit", 200)), 500)
        events = CollaborationRoomService.list_events(
            room=room,
            after_sequence=after_sequence,
            limit=limit,
        )
        serializer = CollaborationRoomEventSerializer(events, many=True)
        return Response(
            APIResponse.get_response(
                data={ 
                    "events": serializer.data,
                    "last_event_sequence": room.last_event_sequence,
                }
            )
        )

    @swagger_auto_schema(
        tags=["collaboration"],
        request_body=CollaborationRoomEventCreateSerializer,
    )
    def post(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_edit(room=room, user=request.user)
        serializer = CollaborationRoomEventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = CollaborationRoomService.append_event(
            room=room,
            actor=request.user,
            payload=serializer.validated_data["payload"],
            source="api",
        )
        event_payload = CollaborationRoomEventSerializer(event).data
        publish_result = {"published": False, "reason": "disabled"}
        if serializer.validated_data["publish_to_centrifugo"]:
            publish_result = CentrifugoService.publish_event(room, event_payload)

        return Response(
            APIResponse.get_response(
                message="Room event stored successfully.",
                data={
                    "event": event_payload,
                    "publish_result": publish_result,
                },
            ),
            status=status.HTTP_201_CREATED,
        )


class CollaborationRoomReplayAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def get(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        CollaborationRoomService.assert_can_view(room=room, user=request.user)
        after_sequence = int(request.query_params.get("after_sequence", 0))
        limit = min(int(request.query_params.get("limit", 200)), 500)
        replay_payload = CollaborationRoomService.replay_events(
            room=room,
            after_sequence=after_sequence,
            limit=limit,
        )
        serializer = CollaborationRoomEventSerializer(
            replay_payload["events"],
            many=True,
        )
        return Response(
            APIResponse.get_response(
                data={
                    "events": serializer.data,
                    "from_sequence": replay_payload["from_sequence"],
                    "to_sequence": replay_payload["to_sequence"],
                    "has_more": replay_payload["has_more"],
                }
            )
        )


class CollaborationRoomRealtimeTokenAPI(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["collaboration"])
    def post(self, request, room_uuid):
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        token_payload = CollaborationRoomService.issue_realtime_tokens(
            room=room,
            user=request.user,
        )
        return Response(APIResponse.get_response(data=token_payload))


class CentrifugoPublishProxyAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        tags=["collaboration"],
        request_body=CollaborationProxyPublishSerializer,
    )
    def post(self, request):
        serializer = CollaborationProxyPublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room_uuid = CollaborationRoomService.parse_room_uuid_from_channel(
            serializer.validated_data["channel"]
        )
        room = CollaborationRoomService.get_room_or_404(room_uuid)
        actor = CollaborationRoomService.get_actor_from_proxy_user(
            serializer.validated_data.get("user")
        )
        if not actor:
            return Response(
                {"error": {"message": "Authenticated actor is required."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        CollaborationRoomService.assert_can_edit(room=room, user=actor)

        event = CollaborationRoomService.append_event(
            room=room,
            actor=actor,
            payload=serializer.validated_data["data"],
            source="centrifugo_publish_proxy",
        )

        return Response(
            {
                "result": {
                    "data": CollaborationRoomEventSerializer(event).data,
                    "skip_history": True,
                }
            }
        )

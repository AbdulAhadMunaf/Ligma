from django.urls import path

from apps.collaboration.api.views import room_api

urlpatterns = [
    path("rooms/", room_api.CollaborationRoomListCreateAPI.as_view()),
    path("rooms/<uuid:room_uuid>/", room_api.CollaborationRoomDetailAPI.as_view()),
    path(
        "rooms/<uuid:room_uuid>/members/",
        room_api.CollaborationRoomMemberListCreateAPI.as_view(),
    ),
    path(
        "rooms/<uuid:room_uuid>/scene/",
        room_api.CollaborationRoomSceneAPI.as_view(),
    ),
    path(
        "rooms/<uuid:room_uuid>/node-access/",
        room_api.CollaborationRoomNodeAccessListCreateAPI.as_view(),
    ),
    path(
        "rooms/<uuid:room_uuid>/events/",
        room_api.CollaborationRoomEventListCreateAPI.as_view(),
    ),
    path(
        "rooms/<uuid:room_uuid>/replay/",
        room_api.CollaborationRoomReplayAPI.as_view(),
    ),
    path(
        "rooms/<uuid:room_uuid>/realtime-token/",
        room_api.CollaborationRoomRealtimeTokenAPI.as_view(),
    ),
    path(
        "centrifugo/publish/",
        room_api.CentrifugoPublishProxyAPI.as_view(),
    ),
]

import time

import jwt
import requests
from django.conf import settings


class CentrifugoService:
    @classmethod
    def build_connection_token(cls, user, room, membership):
        now = int(time.time())
        payload = {
            "sub": str(user.id),
            "exp": now + settings.CENTRIFUGO_TOKEN_TTL_SECONDS,
            "info": {
                "room_id": str(room.room_uuid),
                "role": membership.role,
                "name": user.name,
                "email": user.email,
            },
        }
        return jwt.encode(
            payload,
            settings.CENTRIFUGO_HMAC_SECRET,
            algorithm="HS256",
        )

    @classmethod
    def build_subscription_token(cls, user, room, membership):
        now = int(time.time())
        payload = {
            "sub": str(user.id),
            "channel": room.channel_name,
            "exp": now + settings.CENTRIFUGO_TOKEN_TTL_SECONDS,
            "info": {
                "room_id": str(room.room_uuid),
                "role": membership.role,
            },
        }
        return jwt.encode(
            payload,
            settings.CENTRIFUGO_HMAC_SECRET,
            algorithm="HS256",
        )

    @classmethod
    def publish_event(cls, room, event_payload):
        if not settings.CENTRIFUGO_HTTP_API_KEY or not settings.CENTRIFUGO_API_URL:
            return {"published": False, "reason": "centrifugo_not_configured"}

        response = requests.post(
            f"{settings.CENTRIFUGO_API_URL.rstrip('/')}/publish",
            json={
                "channel": room.channel_name,
                "data": event_payload,
            },
            headers={
                "Content-Type": "application/json",
                "X-API-Key": settings.CENTRIFUGO_HTTP_API_KEY,
            },
            timeout=settings.CENTRIFUGO_HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return {"published": True, "result": response.json()}


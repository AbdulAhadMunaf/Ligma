from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Sequence

import requests
from django.conf import settings

from apps.ai_tasks.choices import AITaskPriorityChoices, AITaskStatusChoices, AITaskTypeChoices
from apps.ai_tasks.contracts import FinalTaskAssertionPayload, GlobalInferenceOutput, PatchInferenceOutput, PatchProposalPayload


class AITaskInferenceService:
    @classmethod
    def build_patch_inference(
        cls,
        *,
        room_uuid: str,
        event_sequence: int,
        patch: PatchProposalPayload,
        snapshot_elements: Sequence[Dict[str, Any]],
    ) -> PatchInferenceOutput:
        content_items = cls._extract_content_items(snapshot_elements=snapshot_elements, node_ids=patch.node_ids)
        tier1_decision = cls._should_analyze_patch(content_items=content_items)
        local_inference = {
            "room_uuid": room_uuid,
            "event_sequence": event_sequence,
            "node_count": len(patch.node_ids),
            "should_analyze": tier1_decision,
            "summary": cls._build_summary(content_items),
        }
        return PatchInferenceOutput(
            patch_id=patch.patch_id,
            tier1_decision=tier1_decision,
            content_items=content_items,
            local_inference=local_inference,
            model_name=cls._resolve_model_name(level=2),
            prompt_tokens=max(1, len(content_items) * 12),
            completion_tokens=max(1, len(content_items) * 8),
            latency_ms=0,
        )

    @classmethod
    def build_global_inference(
        cls,
        *,
        room_uuid: str,
        patch_outputs: Sequence[PatchInferenceOutput],
    ) -> GlobalInferenceOutput:
        tasks_by_uid: Dict[str, FinalTaskAssertionPayload] = {}
        for patch_output in patch_outputs:
            if not patch_output.tier1_decision:
                continue
            for item in patch_output.content_items:
                task_payload = cls._build_task_payload(room_uuid=room_uuid, patch_output=patch_output, item=item)
                tasks_by_uid[task_payload.task_uid] = task_payload

        return GlobalInferenceOutput(
            tasks=sorted(tasks_by_uid.values(), key=lambda item: item.task_uid),
            global_inference={"patch_count": len(patch_outputs), "task_count": len(tasks_by_uid)},
        )

    @classmethod
    def _extract_content_items(
        cls,
        *,
        snapshot_elements: Sequence[Dict[str, Any]],
        node_ids: Sequence[str],
    ) -> List[Dict[str, Any]]:
        node_map = {
            element.get("id"): element
            for element in snapshot_elements
            if isinstance(element, dict) and element.get("id")
        }
        content_items: List[Dict[str, Any]] = []
        for node_id in node_ids:
            node = node_map.get(node_id, {})
            text_value = str(node.get("text") or node.get("label") or node.get("name") or "").strip()
            item = {
                "node_id": node_id,
                "type": node.get("type", "unknown"),
                "text": text_value,
                "metadata": {
                    key: value
                    for key, value in node.items()
                    if key not in {"id", "text", "label", "name"}
                },
            }
            if text_value or node.get("type") in {"text", "sticky", "note", "shape"}:
                content_items.append(item)
        return content_items

    @classmethod
    def _should_analyze_patch(cls, *, content_items: Sequence[Dict[str, Any]]) -> bool:
        haystack = " ".join([str(item.get("text", "")) for item in content_items if item.get("text")]).lower()
        trigger_words = ("todo", "fix", "bug", "need", "should", "question", "blocker", "refactor")
        return bool(haystack) and any(word in haystack for word in trigger_words)

    @classmethod
    def _build_summary(cls, content_items: Sequence[Dict[str, Any]]) -> str:
        texts = [str(item.get("text", "")).strip() for item in content_items if item.get("text")]
        if not texts:
            return "No textual content detected."
        return " / ".join(texts[:3])[:240]

    @classmethod
    def _build_task_payload(
        cls,
        *,
        room_uuid: str,
        patch_output: PatchInferenceOutput,
        item: Dict[str, Any],
    ) -> FinalTaskAssertionPayload:
        title = cls._normalize_title(item.get("text") or item.get("type") or "AI task")
        task_type = cls._infer_task_type(title)
        priority = cls._infer_priority(title)
        task_uid_source = f"{room_uuid}|{patch_output.patch_id}|{title}|{task_type}"
        task_uid = hashlib.sha1(task_uid_source.encode("utf-8")).hexdigest()[:16]
        origin_node_ids = [str(item.get("node_id"))] if item.get("node_id") else []
        return FinalTaskAssertionPayload(
            task_uid=task_uid,
            title=title,
            task_type=task_type,
            priority=priority,
            status=AITaskStatusChoices.OPEN,
            depends_on_uids=[],
            origin_node_ids=origin_node_ids,
            confidence=0.72 if patch_output.tier1_decision else 0.4,
            metadata={"patch_id": patch_output.patch_id, "source_tier": "tier_2_patch", "model_name": patch_output.model_name},
        )

    @staticmethod
    def _normalize_title(value: str) -> str:
        value = " ".join(str(value).replace("\n", " ").split())
        return value[:255] or "AI task"

    @staticmethod
    def _infer_task_type(title: str) -> str:
        lower_title = title.lower()
        if "?" in title:
            return AITaskTypeChoices.QUESTION
        if any(word in lower_title for word in ("decide", "decision", "choose", "approve")):
            return AITaskTypeChoices.DECISION
        if any(word in lower_title for word in ("reference", "link", "doc")):
            return AITaskTypeChoices.REFERENCE
        return AITaskTypeChoices.ACTION

    @staticmethod
    def _infer_priority(title: str) -> str:
        lower_title = title.lower()
        if any(word in lower_title for word in ("urgent", "blocker", "critical")):
            return AITaskPriorityChoices.URGENT
        if any(word in lower_title for word in ("fix", "bug", "issue", "error")):
            return AITaskPriorityChoices.HIGH
        return AITaskPriorityChoices.MEDIUM

    @classmethod
    def _resolve_model_name(cls, level: int) -> str:
        return {1: getattr(settings, "AI_TIER1_MODEL", "openrouter/auto"), 2: getattr(settings, "AI_TIER2_MODEL", "openrouter/auto"), 3: getattr(settings, "AI_TIER3_MODEL", "openrouter/auto")}.get(level, "openrouter/auto")

    @classmethod
    def resolve_openrouter_models(cls) -> List[Dict[str, Any]]:
        if not settings.OPENROUTER_API_KEY:
            return []

        response = requests.get(
            f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/models",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER,
                "X-Title": settings.OPENROUTER_APP_NAME,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("data", [])
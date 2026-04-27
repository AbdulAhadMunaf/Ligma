from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PipelineContractBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IncomingEventContext(PipelineContractBase):
    room_uuid: UUID
    event_uuid: UUID
    event_sequence: int
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    snapshot: Dict[str, Any] = Field(default_factory=dict)


class PatchProposalPayload(PipelineContractBase):
    patch_id: str
    node_ids: List[str] = Field(default_factory=list)
    centroid_x: int = 0
    centroid_y: int = 0
    bbox: Dict[str, int] = Field(default_factory=dict)
    patch_hash: str


class PatchInferenceOutput(PipelineContractBase):
    patch_id: str
    tier1_decision: bool
    content_items: List[Dict[str, Any]] = Field(default_factory=list)
    local_inference: Dict[str, Any] = Field(default_factory=dict)
    model_name: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


class FinalTaskAssertionPayload(PipelineContractBase):
    task_uid: str
    title: str
    task_type: str
    priority: str
    status: str
    depends_on_uids: List[str] = Field(default_factory=list)
    origin_node_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GlobalInferenceOutput(PipelineContractBase):
    tasks: List[FinalTaskAssertionPayload] = Field(default_factory=list)
    global_inference: Dict[str, Any] = Field(default_factory=dict)
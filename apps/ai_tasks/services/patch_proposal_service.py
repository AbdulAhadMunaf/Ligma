from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence

from django.conf import settings

from apps.ai_tasks.contracts import IncomingEventContext, PatchProposalPayload


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    x: int
    y: int
    raw: dict


class AIPatchProposalService:
    @classmethod
    def build_patch_proposals(cls, context: IncomingEventContext) -> List[PatchProposalPayload]:
        nodes = cls._collect_changed_nodes(context)
        if not nodes:
            return []

        clusters = cls._cluster_nodes(nodes)
        proposals = []
        for index, cluster in enumerate(clusters, start=1):
            proposals.append(cls._build_proposal(cluster=cluster, index=index))
        return proposals

    @classmethod
    def _collect_changed_nodes(cls, context: IncomingEventContext) -> List[NodeRecord]:
        elements = {
            element.get("id"): element
            for element in (context.snapshot.get("elements") or [])
            if isinstance(element, dict) and element.get("id")
        }
        node_ids = cls._extract_node_ids(context.payload)
        records: List[NodeRecord] = []
        for node_id in node_ids:
            node = elements.get(node_id) or {}
            records.append(
                NodeRecord(
                    node_id=node_id,
                    x=cls._extract_coordinate(node, "x"),
                    y=cls._extract_coordinate(node, "y"),
                    raw=node,
                )
            )
        return records

    @classmethod
    def _extract_node_ids(cls, payload: Dict) -> List[str]:
        node_ids = []
        for operation in payload.get("operations", []):
            op_name = operation.get("op")
            node_id = operation.get("node_id") or operation.get("element", {}).get("id")
            if op_name in {"element.create", "element.update", "element.delete", "text.patch", "node_acl.set"} and node_id:
                node_ids.append(str(node_id))
            elif op_name in {"app_state.update", "files.update"}:
                continue
        return list(dict.fromkeys(node_ids))

    @staticmethod
    def _extract_coordinate(node: dict, key: str) -> int:
        value = node.get(key, 0)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _cluster_nodes(cls, nodes: Sequence[NodeRecord]) -> List[List[NodeRecord]]:
        threshold_x = getattr(settings, "AI_PATCH_THRESHOLD_X", 280)
        threshold_y = getattr(settings, "AI_PATCH_THRESHOLD_Y", 220)
        grouped: Dict[tuple, List[NodeRecord]] = defaultdict(list)
        for node in nodes:
            bucket = (
                node.x // threshold_x if threshold_x else 0,
                node.y // threshold_y if threshold_y else 0,
            )
            grouped[bucket].append(node)

        clusters = []
        for _, cluster_nodes in sorted(grouped.items(), key=lambda item: item[0]):
            clusters.append(sorted(cluster_nodes, key=lambda item: item.node_id)[:40])
        return clusters

    @classmethod
    def _build_proposal(cls, *, cluster: Sequence[NodeRecord], index: int) -> PatchProposalPayload:
        node_ids = sorted(node.node_id for node in cluster)
        xs = [node.x for node in cluster]
        ys = [node.y for node in cluster]
        bbox = {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
        }
        centroid_x = int(sum(xs) / len(xs)) if xs else 0
        centroid_y = int(sum(ys) / len(ys)) if ys else 0
        digest = hashlib.sha1("|".join([*node_ids, str(bbox)]).encode("utf-8")).hexdigest()
        return PatchProposalPayload(
            patch_id=f"patch-{index:03d}",
            node_ids=node_ids,
            centroid_x=centroid_x,
            centroid_y=centroid_y,
            bbox=bbox,
            patch_hash=digest,
        )
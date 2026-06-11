from __future__ import annotations

from dataclasses import dataclass

from .config import Roi
from .target_distance import BBox, bbox_center


@dataclass(frozen=True)
class SafetyDecision:
    safe: bool
    reason: str = "safe"


def point_in_roi(point: tuple[float, float], roi: Roi) -> bool:
    if roi.is_empty:
        return False
    x, y = point
    left, top, right, bottom = roi.as_xyxy()
    return left <= x <= right and top <= y <= bottom


def evaluate_target_safety(
    bbox: BBox | None,
    forbidden_zone: Roi | None,
    enabled: bool = True,
    forbidden_zone_enabled: bool = True,
) -> SafetyDecision:
    if not enabled:
        return SafetyDecision(safe=True, reason="safety disabled")
    if bbox is None:
        return SafetyDecision(safe=False, reason="no target")
    if forbidden_zone_enabled and forbidden_zone is not None:
        if point_in_roi(bbox_center(bbox), forbidden_zone):
            return SafetyDecision(safe=False, reason="target in forbidden zone")
    return SafetyDecision(safe=True)

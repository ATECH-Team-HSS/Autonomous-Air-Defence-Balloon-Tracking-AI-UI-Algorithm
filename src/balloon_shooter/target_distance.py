from __future__ import annotations

from collections.abc import Sequence

BBox = Sequence[float]
Point = tuple[float, float]


def bbox_center(bbox: BBox) -> Point:
    x1, y1, x2, y2 = bbox[:4]
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def pixel_offset(bbox: BBox, frame_center: Point) -> Point:
    target_x, target_y = bbox_center(bbox)
    return (frame_center[0] - target_x, frame_center[1] - target_y)


def is_within_threshold(
    bbox: BBox,
    frame_center: Point,
    x_threshold: float,
    y_threshold: float,
) -> bool:
    dx, dy = pixel_offset(bbox, frame_center)
    return abs(dx) <= x_threshold and abs(dy) <= y_threshold

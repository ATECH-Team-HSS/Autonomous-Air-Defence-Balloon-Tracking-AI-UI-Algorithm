from __future__ import annotations

from collections.abc import Sequence

import cv2

from .config import Roi

Color = tuple[int, int, int]
GREEN: Color = (0, 255, 0)
RED: Color = (0, 0, 255)
BLUE: Color = (255, 0, 0)
YELLOW: Color = (0, 255, 255)


def draw_crosshair(
    frame,
    x: int,
    y: int,
    size: int,
    inner_radius: int,
    outer_radius: int,
    color: Color = RED,
    thickness: int = 1,
) -> None:
    cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
    cv2.line(frame, (x, y - size), (x, y + size), color, thickness)
    cv2.circle(frame, (x, y), inner_radius, color, thickness)
    cv2.circle(frame, (x, y), outer_radius, color, thickness)


def draw_detections(
    frame,
    detections: Sequence[Sequence[float]],
    class_names: Sequence[str],
) -> None:
    for detection in detections:
        x1, y1, x2, y2, confidence, class_id = detection
        left, top, right, bottom = map(int, (x1, y1, x2, y2))
        label = _class_label(class_names, int(class_id))
        cv2.rectangle(frame, (left, top), (right, bottom), GREEN, 2)
        cv2.putText(
            frame,
            f"{label} {confidence:.2f}",
            (left, max(20, top - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            GREEN,
            2,
        )


def draw_target(
    frame,
    track: Sequence[float],
    class_names: Sequence[str],
    safe: bool,
) -> None:
    x1, y1, x2, y2, track_id, class_id = track
    left, top, right, bottom = map(int, (x1, y1, x2, y2))
    color = GREEN if safe else RED
    center_x = int((left + right) / 2)
    center_y = int((top + bottom) / 2)
    label = _class_label(class_names, int(class_id))

    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.circle(frame, (center_x, center_y), 5, color, -1)
    cv2.putText(
        frame,
        f"Target {int(track_id)}: {label}",
        (left, max(20, top - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
    )


def draw_forbidden_zone(frame, roi: Roi, enabled: bool) -> None:
    if not enabled or roi.is_empty:
        return
    left, top, right, bottom = roi.as_xyxy()
    cv2.rectangle(frame, (left, top), (right, bottom), RED, 2)
    cv2.putText(
        frame,
        "Forbidden zone",
        (left, max(20, top - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        RED,
        2,
    )


def draw_status(frame, text: str, line: int = 0, color: Color = YELLOW) -> None:
    y = 30 + line * 28
    cv2.putText(
        frame,
        text,
        (10, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
    )


def _class_label(class_names: Sequence[str], class_id: int) -> str:
    if 0 <= class_id < len(class_names):
        return class_names[class_id]
    return f"class {class_id}"

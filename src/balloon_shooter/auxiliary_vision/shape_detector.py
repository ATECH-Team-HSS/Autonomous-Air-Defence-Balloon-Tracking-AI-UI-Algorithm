from __future__ import annotations

import cv2
import numpy as np

ColorRange = tuple[np.ndarray, np.ndarray]

HSV_RANGES: dict[str, tuple[ColorRange, ...]] = {
    "Red": (
        (np.array([0, 100, 100]), np.array([10, 255, 255])),
        (np.array([160, 100, 100]), np.array([179, 255, 255])),
    ),
    "Green": ((np.array([50, 100, 100]), np.array([70, 255, 255])),),
    "Blue": ((np.array([98, 50, 50]), np.array([139, 255, 255])),),
}


def detect_shapes(frame, min_area: float = 400.0) -> list[str]:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    shapes: list[str] = []

    for color, ranges in HSV_RANGES.items():
        mask = _mask_for_ranges(hsv, ranges)
        shapes.extend(_find_shapes(mask, color, min_area))

    return shapes


def _mask_for_ranges(hsv, ranges: tuple[ColorRange, ...]):
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lower, upper in ranges:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
    return mask


def _find_shapes(mask, color: str, min_area: float) -> list[str]:
    found: list[str] = []
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        perimeter = cv2.arcLength(contour, True)
        approximation = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        shape = _shape_name(len(approximation))
        found.append(f"{color} {shape}")

    return found


def _shape_name(vertices: int) -> str:
    if vertices == 3:
        return "Triangle"
    if vertices == 4:
        return "Square"
    return "Circle"

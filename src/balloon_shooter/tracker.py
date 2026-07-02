from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from filterpy.kalman import KalmanFilter


def iou(bbox_a: Iterable[float], bbox_b: Iterable[float]) -> float:
    ax1, ay1, ax2, ay2 = bbox_a
    bx1, by1, bx2, by2 = bbox_b

    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)
    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return float(intersection / (area_a + area_b - intersection))


def convert_bbox_to_z(bbox: Iterable[float]) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    center_x = x1 + width / 2.0
    center_y = y1 + height / 2.0
    scale = width * height
    ratio = width / float(height) if height != 0 else 0.0
    return np.array([center_x, center_y, scale, ratio]).reshape((4, 1))


def convert_x_to_bbox(state: np.ndarray) -> np.ndarray:
    flat_state = np.asarray(state).reshape(-1)
    center_x = float(flat_state[0])
    center_y = float(flat_state[1])
    scale = max(float(flat_state[2]), 0.0)
    ratio = max(float(flat_state[3]), 0.0)
    width = np.sqrt(scale * ratio) if ratio > 0 else 0.0
    height = scale / width if width > 0 else 0.0
    return np.array(
        [
            center_x - width / 2.0,
            center_y - height / 2.0,
            center_x + width / 2.0,
            center_y + height / 2.0,
        ]
    )


class KalmanBoxTracker:
    count = 0

    def __init__(self, bbox: Iterable[float], class_id: int) -> None:
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.eye(7)
        self.kf.F[0, 4] = 1.0
        self.kf.F[1, 5] = 1.0
        self.kf.F[2, 6] = 1.0
        self.kf.H = np.eye(4, 7)
        self.kf.P *= 10.0
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.Q = np.eye(7) * 0.1
        self.kf.R = np.eye(4)
        self.kf.x[:4] = convert_bbox_to_z(bbox)

        KalmanBoxTracker.count += 1
        self.id = KalmanBoxTracker.count
        self.class_id = class_id
        self.time_since_update = 0
        self.age = 0
        self.hit_streak = 0
        self.history: list[np.ndarray] = []

    def update(self, bbox: Iterable[float]) -> None:
        self.history = []
        self.time_since_update = 0
        self.hit_streak += 1
        self.kf.update(convert_bbox_to_z(bbox))

    def predict(self) -> np.ndarray:
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(convert_x_to_bbox(self.kf.x))
        return self.history[-1]

    def get_state(self) -> np.ndarray:
        return convert_x_to_bbox(self.kf.x)


class Tracker:
    """SORT-style tracker using a Kalman filter and IoU matching."""

    def __init__(self, max_age: int = 1, iou_threshold: float = 0.3) -> None:
        self.max_age = max_age
        self.iou_threshold = iou_threshold
        self.trackers: list[KalmanBoxTracker] = []

    def update(self, detections: Iterable[Iterable[float]] | np.ndarray) -> np.ndarray:
        detection_array = _as_detection_array(detections)

        for tracker in self.trackers:
            tracker.predict()

        if detection_array.size == 0:
            self.trackers = [
                tracker
                for tracker in self.trackers
                if tracker.time_since_update <= self.max_age
            ]
            return np.empty((0, 6))

        if not self.trackers:
            self.trackers = [
                KalmanBoxTracker(detection[:4], int(detection[5]))
                for detection in detection_array
            ]
            return self._current_tracks()

        matched, unmatched_detections = self._match(detection_array)

        for detection_index, tracker_index in matched:
            self.trackers[tracker_index].update(detection_array[detection_index, :4])

        for detection_index in unmatched_detections:
            detection = detection_array[detection_index]
            self.trackers.append(KalmanBoxTracker(detection[:4], int(detection[5])))

        self.trackers = [
            tracker
            for tracker in self.trackers
            if tracker.time_since_update <= self.max_age
        ]
        return self._current_tracks(updated_only=True)

    def _match(self, detections: np.ndarray) -> tuple[list[tuple[int, int]], list[int]]:
        tracker_boxes = np.array([tracker.get_state() for tracker in self.trackers])
        iou_matrix = np.zeros((len(detections), len(self.trackers)), dtype=float)
        for detection_index, detection in enumerate(detections):
            for tracker_index, tracker_box in enumerate(tracker_boxes):
                iou_matrix[detection_index, tracker_index] = iou(
                    detection[:4],
                    tracker_box,
                )

        detection_indices, tracker_indices = _assign_by_iou(iou_matrix)
        matched: list[tuple[int, int]] = []
        unmatched_detections: list[int] = []

        for detection_index, tracker_index in zip(
            detection_indices,
            tracker_indices,
            strict=True,
        ):
            if iou_matrix[detection_index, tracker_index] < self.iou_threshold:
                unmatched_detections.append(detection_index)
            else:
                matched.append((detection_index, tracker_index))

        assigned_detection_indices = set(detection_indices)
        unmatched_detections.extend(
            detection_index
            for detection_index in range(len(detections))
            if detection_index not in assigned_detection_indices
        )
        return matched, unmatched_detections

    def _current_tracks(self, updated_only: bool = False) -> np.ndarray:
        outputs = []
        for tracker in self.trackers:
            if updated_only and tracker.time_since_update != 0:
                continue
            x1, y1, x2, y2 = tracker.get_state()
            outputs.append([x1, y1, x2, y2, tracker.id, tracker.class_id])
        if not outputs:
            return np.empty((0, 6))
        return np.asarray(outputs, dtype=float)


def _as_detection_array(
    detections: Iterable[Iterable[float]] | np.ndarray,
) -> np.ndarray:
    detection_array = np.asarray(detections, dtype=float)
    if detection_array.size == 0:
        return np.empty((0, 6), dtype=float)
    return detection_array.reshape((-1, 6))


def _assign_by_iou(iou_matrix: np.ndarray) -> tuple[list[int], list[int]]:
    try:
        from scipy.optimize import linear_sum_assignment

        detection_indices, tracker_indices = linear_sum_assignment(1.0 - iou_matrix)
        return list(detection_indices), list(tracker_indices)
    except ImportError:
        return _greedy_assign(iou_matrix)


def _greedy_assign(iou_matrix: np.ndarray) -> tuple[list[int], list[int]]:
    detection_indices: list[int] = []
    tracker_indices: list[int] = []
    remaining = iou_matrix.copy()

    while remaining.size:
        detection_index, tracker_index = np.unravel_index(
            np.argmax(remaining),
            remaining.shape,
        )
        if remaining[detection_index, tracker_index] <= 0:
            break
        detection_indices.append(int(detection_index))
        tracker_indices.append(int(tracker_index))
        remaining[detection_index, :] = -1
        remaining[:, tracker_index] = -1

    return detection_indices, tracker_indices

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

BLUE_CLASS_ID = 0
RED_CLASS_ID = 1


def select_candidate_track(
    tracks: Iterable[Iterable[float]],
    min_width: float,
    min_height: float,
    color_strategy: str,
) -> np.ndarray | None:
    track_array = _as_track_array(tracks)
    if track_array.size == 0:
        return None

    valid_tracks = [
        track
        for track in track_array
        if (track[2] - track[0]) >= min_width and (track[3] - track[1]) >= min_height
    ]
    if not valid_tracks:
        return None

    strategy = color_strategy.lower()
    if strategy == "red_only":
        valid_tracks = [
            track for track in valid_tracks if int(track[5]) == RED_CLASS_ID
        ]
    elif strategy == "blue_only":
        valid_tracks = [
            track for track in valid_tracks if int(track[5]) == BLUE_CLASS_ID
        ]
    elif strategy == "red_then_blue":
        red_tracks = [track for track in valid_tracks if int(track[5]) == RED_CLASS_ID]
        blue_tracks = [
            track for track in valid_tracks if int(track[5]) == BLUE_CLASS_ID
        ]
        valid_tracks = red_tracks if red_tracks else blue_tracks
    elif strategy != "all":
        raise ValueError(
            "color_strategy must be one of: red_only, blue_only, red_then_blue, all"
        )

    if not valid_tracks:
        return None

    return min(
        valid_tracks, key=lambda track: (track[2] - track[0]) * (track[3] - track[1])
    )


@dataclass
class TargetSelector:
    min_width: float
    min_height: float
    color_strategy: str
    confirmation_duration: float
    confirmed_target_id: int | None = None
    last_best_id: int | None = None
    confirm_start_time: float | None = None

    def update(
        self,
        tracks: Iterable[Iterable[float]],
        now: float | None = None,
    ) -> np.ndarray | None:
        track_array = _as_track_array(tracks)
        now = time.time() if now is None else now

        if self.confirmed_target_id is not None:
            target = _find_track_by_id(track_array, self.confirmed_target_id)
            if target is not None:
                return target
            self.reset()

        best_track = select_candidate_track(
            track_array,
            self.min_width,
            self.min_height,
            self.color_strategy,
        )
        if best_track is None:
            self.last_best_id = None
            self.confirm_start_time = None
            return None

        best_id = int(best_track[4])
        if self.last_best_id != best_id:
            self.last_best_id = best_id
            self.confirm_start_time = now
            return None

        if self.confirm_start_time is not None:
            if now - self.confirm_start_time >= self.confirmation_duration:
                self.confirmed_target_id = best_id
                return best_track

        return None

    def reset(self) -> None:
        self.confirmed_target_id = None
        self.last_best_id = None
        self.confirm_start_time = None


def _as_track_array(tracks: Iterable[Iterable[float]]) -> np.ndarray:
    track_array = np.asarray(list(tracks), dtype=float)
    if track_array.size == 0:
        return np.empty((0, 6), dtype=float)
    return track_array.reshape((-1, 6))


def _find_track_by_id(tracks: np.ndarray, track_id: int) -> np.ndarray | None:
    for track in tracks:
        if int(track[4]) == track_id:
            return track
    return None

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "balloon_shooter"

from .config import AppConfig, load_config
from .detector import Detector
from .fps_counter import FPSCounter
from .overlays import (
    draw_crosshair,
    draw_detections,
    draw_forbidden_zone,
    draw_status,
    draw_target,
)
from .safety import evaluate_target_safety
from .target_distance import is_within_threshold
from .targeting import TargetSelector
from .tracker import Tracker


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = load_config(args.config)
    return run(config)


def run(config: AppConfig) -> int:
    try:
        detector = Detector(
            model_path=config.video.model_path,
            confidence_threshold=config.video.confidence_threshold,
            iou_threshold=config.video.iou_threshold,
            device_preference=config.video.device,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        print("Place your local YOLO weights at that path or update video.model_path.")
        print("Example: video.model_path: \"C:/path/to/your/best.pt\"")
        return 1

    tracker = Tracker(
        max_age=config.tracking.max_age,
        iou_threshold=config.tracking.iou_threshold,
    )
    selector = TargetSelector(
        min_width=config.targeting.min_bbox_width,
        min_height=config.targeting.min_bbox_height,
        color_strategy=config.targeting.color_strategy,
        confirmation_duration=config.targeting.confirmation_duration,
    )
    fps_counter = FPSCounter(avg_over=30)

    capture = cv2.VideoCapture(config.video.source)
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.video.frame_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.video.frame_height)
    capture.set(cv2.CAP_PROP_FPS, 30)

    if not capture.isOpened():
        print(f"ERROR: cannot open video source {config.video.source!r}")
        return 1

    if config.targeting.startup_delay_seconds > 0:
        time.sleep(config.targeting.startup_delay_seconds)

    try:
        return _run_loop(config, detector, tracker, selector, fps_counter, capture)
    finally:
        capture.release()
        cv2.destroyAllWindows()


def _run_loop(
    config: AppConfig,
    detector: Detector,
    tracker: Tracker,
    selector: TargetSelector,
    fps_counter: FPSCounter,
    capture: cv2.VideoCapture,
) -> int:
    frame_size = (config.video.frame_width, config.video.frame_height)
    crosshair_center = _crosshair_center(config)

    while True:
        ret, frame = capture.read()
        if not ret:
            print("WARNING: failed to read frame from video source.")
            return 1

        frame = cv2.resize(frame, frame_size)
        detections = detector.detect(frame)
        tracks = tracker.update(detections)
        target_track = selector.update(tracks)

        draw_detections(frame, detections, config.video.class_names)
        draw_forbidden_zone(
            frame,
            config.safety.forbidden_fire_zone,
            config.safety.forbidden_fire_zone_enabled,
        )

        target_safe = False
        within_crosshair = False
        safety_reason = "no target"
        if target_track is not None:
            bbox = target_track[:4]
            safety = evaluate_target_safety(
                bbox,
                config.safety.forbidden_fire_zone,
                enabled=config.safety.enabled,
                forbidden_zone_enabled=config.safety.forbidden_fire_zone_enabled,
            )
            target_safe = safety.safe
            safety_reason = safety.reason
            within_crosshair = is_within_threshold(
                bbox,
                crosshair_center,
                config.targeting.x_tolerance,
                config.targeting.y_tolerance,
            )
            draw_target(frame, target_track, config.video.class_names, target_safe)

        draw_crosshair(
            frame,
            crosshair_center[0],
            crosshair_center[1],
            config.crosshair.size,
            config.crosshair.inner_radius,
            config.crosshair.outer_radius,
        )

        fps = fps_counter.update()
        draw_status(frame, f"FPS: {fps:.2f}", line=0)
        draw_status(frame, f"Target aligned: {within_crosshair}", line=1)
        draw_status(frame, f"Safety: {safety_reason}", line=2)
        draw_status(frame, "Firing output: disabled", line=3)
        print(
            "Target aligned: "
            f"{within_crosshair}, safety: {target_safe}, reason: {safety_reason}"
        )

        cv2.imshow(config.video.window_name, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return 0


def _crosshair_center(config: AppConfig) -> tuple[int, int]:
    x = config.crosshair.x
    y = config.crosshair.y
    if x is None:
        x = config.video.frame_width // 2
    if y is None:
        y = config.video.frame_height // 2
    return (x, y)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the balloon detector demo.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to the YAML configuration file.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())

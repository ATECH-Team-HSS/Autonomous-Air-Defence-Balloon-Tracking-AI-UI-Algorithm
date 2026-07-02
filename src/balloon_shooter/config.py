from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

DevicePreference = Literal["auto", "cuda", "cpu"]
VideoSource = int | str


@dataclass(frozen=True)
class Roi:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    @classmethod
    def from_value(cls, value: Any) -> Roi:
        if value is None:
            return cls()
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            width = value.get("width", value.get("w", 0))
            height = value.get("height", value.get("h", 0))
            return cls(
                x=int(value.get("x", 0)),
                y=int(value.get("y", 0)),
                width=int(width),
                height=int(height),
            )
        if isinstance(value, (list, tuple)) and len(value) == 4:
            x, y, width, height = value
            return cls(int(x), int(y), int(width), int(height))
        raise ValueError(f"Invalid ROI value: {value!r}")

    @property
    def is_empty(self) -> bool:
        return self.width <= 0 or self.height <= 0

    def as_xyxy(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass(frozen=True)
class VideoConfig:
    source: VideoSource = 0
    frame_width: int = 1280
    frame_height: int = 720
    window_name: str = "Balloon Detection"
    model_path: Path = Path("models/best.pt")
    class_names: tuple[str, ...] = ("Blue Balloon", "Red Balloon")
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    device: DevicePreference = "auto"


@dataclass(frozen=True)
class TrackingConfig:
    max_age: int = 1
    iou_threshold: float = 0.3


@dataclass(frozen=True)
class TargetingConfig:
    min_bbox_width: int = 20
    min_bbox_height: int = 20
    color_strategy: str = "red_only"
    confirmation_duration: float = 0.3
    startup_delay_seconds: float = 1.0
    x_tolerance: int = 50
    y_tolerance: int = 50


@dataclass(frozen=True)
class CrosshairConfig:
    x: int | None = None
    y: int | None = None
    size: int = 60
    inner_radius: int = 20
    outer_radius: int = 40


@dataclass(frozen=True)
class SafetyConfig:
    enabled: bool = True
    forbidden_fire_zone_enabled: bool = True
    forbidden_fire_zone: Roi = Roi()


@dataclass(frozen=True)
class AuxiliaryVisionConfig:
    qr_roi: Roi = Roi(100, 50, 180, 180)
    shape_roi: Roi = Roi(320, 50, 180, 180)
    window_name: str = "Task Command Demo"


@dataclass(frozen=True)
class FutureSerialConfig:
    enabled: bool = False
    port: str = ""
    baud_rate: int = 115200


@dataclass(frozen=True)
class AppConfig:
    video: VideoConfig
    tracking: TrackingConfig
    targeting: TargetingConfig
    crosshair: CrosshairConfig
    safety: SafetyConfig
    auxiliary_vision: AuxiliaryVisionConfig
    future_serial: FutureSerialConfig


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path).expanduser()
    data = _read_yaml(config_path)
    base_dir = config_path.resolve().parent

    video = _section(data, "video")
    tracking = _section(data, "tracking")
    targeting = _section(data, "targeting")
    crosshair = _section(data, "crosshair")
    safety = _section(data, "safety")
    auxiliary = _section(data, "auxiliary_vision")
    future_serial = _section(data, "future_serial")

    return AppConfig(
        video=_load_video_config(video, base_dir),
        tracking=TrackingConfig(
            max_age=int(tracking.get("max_age", 1)),
            iou_threshold=float(tracking.get("iou_threshold", 0.3)),
        ),
        targeting=TargetingConfig(
            min_bbox_width=int(targeting.get("min_bbox_width", 20)),
            min_bbox_height=int(targeting.get("min_bbox_height", 20)),
            color_strategy=str(targeting.get("color_strategy", "red_only")),
            confirmation_duration=float(targeting.get("confirmation_duration", 0.3)),
            startup_delay_seconds=float(targeting.get("startup_delay_seconds", 1.0)),
            x_tolerance=int(
                targeting.get("x_tolerance", targeting.get("x_changer", 50))
            ),
            y_tolerance=int(
                targeting.get("y_tolerance", targeting.get("y_changer", 50))
            ),
        ),
        crosshair=CrosshairConfig(
            x=_optional_int(crosshair.get("x")),
            y=_optional_int(crosshair.get("y")),
            size=int(crosshair.get("size", 60)),
            inner_radius=int(crosshair.get("inner_radius", 20)),
            outer_radius=int(crosshair.get("outer_radius", 40)),
        ),
        safety=_load_safety_config(safety),
        auxiliary_vision=AuxiliaryVisionConfig(
            qr_roi=Roi.from_value(auxiliary.get("qr_roi", [100, 50, 180, 180])),
            shape_roi=Roi.from_value(auxiliary.get("shape_roi", [320, 50, 180, 180])),
            window_name=str(auxiliary.get("window_name", "Task Command Demo")),
        ),
        future_serial=FutureSerialConfig(
            enabled=bool(future_serial.get("enabled", False)),
            port=str(future_serial.get("port", "")),
            baud_rate=int(future_serial.get("baud_rate", 115200)),
        ),
    )


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as config_file:
        loaded = yaml.safe_load(config_file) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return loaded


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{key}' must be a mapping.")
    return value


def _load_video_config(video: dict[str, Any], base_dir: Path) -> VideoConfig:
    model_path = Path(str(video.get("model_path", "models/best.pt"))).expanduser()
    if not model_path.is_absolute():
        model_path = base_dir / model_path

    source = video.get("source", video.get("camera_index", 0))
    class_names = tuple(str(name) for name in video.get("class_names", []))
    if not class_names:
        class_names = ("Blue Balloon", "Red Balloon")

    device = str(video.get("device", "auto")).lower()
    if device not in {"auto", "cuda", "cpu"}:
        raise ValueError("video.device must be one of: auto, cuda, cpu")

    return VideoConfig(
        source=_coerce_video_source(source),
        frame_width=int(
            video.get("frame_width", video.get("target_size", [1280, 720])[0])
        ),
        frame_height=int(
            video.get("frame_height", video.get("target_size", [1280, 720])[1])
        ),
        window_name=str(video.get("window_name", "Balloon Detection")),
        model_path=model_path,
        class_names=class_names,
        confidence_threshold=float(
            video.get("confidence_threshold", video.get("conf_threshold", 0.5))
        ),
        iou_threshold=float(video.get("iou_threshold", 0.45)),
        device=device,  # type: ignore[arg-type]
    )


def _load_safety_config(safety: dict[str, Any]) -> SafetyConfig:
    forbidden = safety.get("forbidden_fire_zone", {})
    if isinstance(forbidden, (list, tuple)):
        return SafetyConfig(
            enabled=bool(safety.get("enabled", True)),
            forbidden_fire_zone_enabled=True,
            forbidden_fire_zone=Roi.from_value(forbidden),
        )
    if forbidden is None:
        forbidden = {}
    if not isinstance(forbidden, dict):
        raise ValueError("safety.forbidden_fire_zone must be a mapping or ROI list.")

    return SafetyConfig(
        enabled=bool(safety.get("enabled", True)),
        forbidden_fire_zone_enabled=bool(forbidden.get("enabled", True)),
        forbidden_fire_zone=Roi.from_value(forbidden.get("rect", forbidden)),
    )


def _coerce_video_source(source: Any) -> VideoSource:
    if isinstance(source, int):
        return source
    if isinstance(source, str):
        stripped = source.strip()
        if stripped.isdigit():
            return int(stripped)
        return stripped
    raise ValueError(f"Unsupported video source: {source!r}")


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)

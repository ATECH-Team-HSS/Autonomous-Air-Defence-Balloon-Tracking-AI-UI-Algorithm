from __future__ import annotations

from pathlib import Path
from typing import Any


class Detector:
    """Small YOLO wrapper returning [x1, y1, x2, y2, confidence, class_id]."""

    def __init__(
        self,
        model_path: str | Path,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device_preference: str = "auto",
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YOLO model weights were not found: {self.model_path}. "
                "Update config.yaml with a local weight file before running inference."
            )

        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self._torch, self.model = self._load_model(device_preference)

    def detect(self, image: Any) -> list[list[float]]:
        detections: list[list[float]] = []
        with self._torch.no_grad():
            result_stream = self.model(
                image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                device=self.device,
                stream=True,
                verbose=False,
            )
            result = next(iter(result_stream))

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            detections.append([x1, y1, x2, y2, confidence, class_id])

        return detections

    def _load_model(self, device_preference: str) -> tuple[Any, Any]:
        import torch
        from ultralytics import YOLO

        self.device = _select_device(torch, device_preference)
        model = YOLO(str(self.model_path))
        model.to(self.device)

        backend_model = getattr(model, "model", None)
        if backend_model is not None:
            if hasattr(backend_model, "fuse"):
                backend_model.fuse()
            if self.device.startswith("cuda") and hasattr(backend_model, "half"):
                backend_model.half()
            if hasattr(backend_model, "eval"):
                backend_model.eval()

        return torch, model


def _select_device(torch_module: Any, preference: str) -> str:
    normalized = preference.lower()
    cuda_available = bool(torch_module.cuda.is_available())

    if normalized == "cpu":
        return "cpu"
    if normalized in {"auto", "cuda"} and cuda_available:
        return "cuda:0"
    if normalized == "cuda" and not cuda_available:
        print("CUDA was requested but is unavailable; falling back to CPU.")
        return "cpu"
    if normalized == "auto":
        return "cpu"

    raise ValueError("device_preference must be one of: auto, cuda, cpu")

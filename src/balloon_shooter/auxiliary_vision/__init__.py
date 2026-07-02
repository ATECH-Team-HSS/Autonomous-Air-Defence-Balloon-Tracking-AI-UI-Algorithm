"""Independent QR-code and shape-detection helpers."""

from .qr_decoder import decode_qr
from .shape_detector import detect_shapes

__all__ = ["decode_qr", "detect_shapes"]

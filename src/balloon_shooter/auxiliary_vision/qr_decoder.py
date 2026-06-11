from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import cv2

Decoder = Callable[[Any], Iterable[Any]]


def decode_qr(
    frame,
    allowed_values: Sequence[str] = ("A", "B"),
    decoder: Decoder | None = None,
) -> str | None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    decode = decoder or _pyzbar_decode

    for code in decode(gray):
        data = _decode_payload(code)
        if data in allowed_values:
            return data
    return None


def _pyzbar_decode(gray_frame) -> Iterable[Any]:
    from pyzbar import pyzbar

    return pyzbar.decode(gray_frame)


def _decode_payload(code: Any) -> str:
    payload = getattr(code, "data", b"")
    if isinstance(payload, bytes):
        return payload.decode("utf-8", errors="replace")
    return str(payload)

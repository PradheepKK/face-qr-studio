# Generate aana image-a real decoders (ZXing + OpenCV) vachu verify pannum.
# "Verified" = required checks ellaam pass + decoded payload exact bytes match.

from dataclasses import dataclass

import cv2
import numpy as np
import zxingcpp

BASE_SIDE = 1200  # ella image-um indha size-ku normalize panni test pannrom


@dataclass
class Check:
    decoder: str  # "zxing" / "opencv"
    variant: str  # "100%", "75%", "50%", "jpeg"
    ok: bool
    required: bool

    @property
    def label(self) -> str:
        return f"{self.decoder}@{self.variant}"


@dataclass
class ValidationReport:
    verified: bool
    checks: list[Check]
    passed: int
    total: int
    required_passed: int
    required_total: int

    def summary(self) -> str:
        return f"{self.passed}/{self.total} checks pass, required {self.required_passed}/{self.required_total}"

    def detail(self) -> str:
        """Header-la anuppa ASCII string: zxing@100%=OK;..."""
        return ";".join(f"{c.label}={'OK' if c.ok else 'FAIL'}{'*' if c.required else ''}" for c in self.checks)


# ---------------------------------------------------------------
# Decoders (preprocessing illa: scanner-a pola direct-a padikkum)
# ---------------------------------------------------------------
def _zxing_matches(gray: np.ndarray, expected: bytes) -> bool:
    """ZXing-la vara ella valid results-um expected-oda exact match aaganum."""
    try:
        results = zxingcpp.read_barcodes(gray, formats=zxingcpp.BarcodeFormat.QRCode)
    except Exception:
        return False
    valid = [r for r in results if r.valid]
    if not valid:
        return False
    for r in valid:
        raw = getattr(r, "bytes", None)
        data = bytes(raw) if raw else r.text.encode("utf-8")
        if data != expected:
            return False
    return True


def _opencv_matches(gray: np.ndarray, expected: bytes) -> bool:
    try:
        text, _, _ = cv2.QRCodeDetector().detectAndDecode(gray)
    except cv2.error:
        return False
    return bool(text) and text.encode("utf-8") == expected


def _resize(gray: np.ndarray, side: int) -> np.ndarray:
    cur = gray.shape[0]
    interp = cv2.INTER_AREA if side < cur else cv2.INTER_CUBIC
    return cv2.resize(gray, (side, side), interpolation=interp)


def _jpeg(gray: np.ndarray, quality: int) -> np.ndarray:
    ok, buf = cv2.imencode(".jpg", gray, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return gray
    return cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def validate(img_bgr: np.ndarray, expected: bytes) -> ValidationReport:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if img_bgr.ndim == 3 else img_bgr
    base = _resize(gray, BASE_SIDE)

    # OpenCV text-a mattum return pannum. Binary payload-na OpenCV check skip.
    try:
        expected.decode("utf-8")
        opencv_applicable = True
    except UnicodeDecodeError:
        opencv_applicable = False

    # (variant name, image, zxing required, opencv required)
    variants = [
        ("100%", base, True, True),
        ("75%", _resize(base, int(BASE_SIDE * 0.75)), True, False),
        ("50%", _resize(base, int(BASE_SIDE * 0.50)), True, False),
        ("jpeg", _jpeg(_resize(base, int(BASE_SIDE * 0.75)), 60), False, False),
    ]

    checks: list[Check] = []
    for name, im, zx_req, cv_req in variants:
        checks.append(Check("zxing", name, _zxing_matches(im, expected), zx_req))
        if opencv_applicable:
            checks.append(Check("opencv", name, _opencv_matches(im, expected), cv_req))

    required = [c for c in checks if c.required]
    req_passed = sum(c.ok for c in required)
    passed = sum(c.ok for c in checks)

    return ValidationReport(
        verified=len(required) > 0 and req_passed == len(required),
        checks=checks,
        passed=passed,
        total=len(checks),
        required_passed=req_passed,
        required_total=len(required),
    )
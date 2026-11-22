# Generate aana image-a real decoders vachu verify pannum.
# "Verified" = ZXing required checks (normal + blur + global binarizer + small size)
# ellaam pass + decoded payload exact bytes match. OpenCV = advisory.

from dataclasses import dataclass

import cv2
import numpy as np
import zxingcpp

BASE_SIDE = 1200


@dataclass
class Check:
    decoder: str
    variant: str
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
        return ";".join(f"{c.label}={'OK' if c.ok else 'FAIL'}{'*' if c.required else ''}" for c in self.checks)


def _zxing_matches(gray: np.ndarray, expected: bytes, binarizer: str | None = None) -> bool:
    """ZXing-la vara ella valid results-um expected-oda exact match aaganum."""
    kwargs = {"formats": zxingcpp.BarcodeFormat.QRCode}
    if binarizer:
        try:
            kwargs["binarizer"] = getattr(zxingcpp.Binarizer, binarizer)
        except AttributeError:
            return False  # indha zxing version-la binarizer option illa
    try:
        results = zxingcpp.read_barcodes(gray, **kwargs)
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


def validate(img_bgr: np.ndarray, expected: bytes) -> ValidationReport:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY) if img_bgr.ndim == 3 else img_bgr
    base = _resize(gray, BASE_SIDE)

    try:
        expected.decode("utf-8")
        opencv_applicable = True
    except UnicodeDecodeError:
        opencv_applicable = False

    s75 = _resize(base, int(BASE_SIDE * 0.75))
    s50 = _resize(base, int(BASE_SIDE * 0.50))
    s35 = _resize(base, int(BASE_SIDE * 0.35))
    blurred = cv2.GaussianBlur(s50, (0, 0), 1.2)  # camera focus maari

    # (name, image, binarizer, zxing required)
    zx_variants = [
        ("100%", base, None, True),
        ("75%", s75, None, True),
        ("50%", s50, None, True),
        ("35%", s35, None, True),
        ("blur", blurred, None, True),
        ("global", s75, "GlobalHistogram", True),
        ("jpeg", _jpeg(s75, 60), None, False),
    ]

    checks: list[Check] = []
    for name, im, binar, req in zx_variants:
        checks.append(Check("zxing", name, _zxing_matches(im, expected, binar), req))

    if opencv_applicable:
        for name, im in (("100%", base), ("75%", s75), ("50%", s50)):
            checks.append(Check("opencv", name, _opencv_matches(im, expected), False))

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
# Payment QR-a decode pannum. ZXing + OpenCV rendaiyum use pannum.
# Payload-a exact bytes-a eduthu vaikkum (Step 8-la compare panna).

import hashlib
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np
import qrcode
import zxingcpp
from qrcode.exceptions import DataOverflowError


class NoQrError(Exception):
    """Image-la readable QR kandupidikka mudiyala."""


# Error correction levels: best (H) mudhal, fit aagala-na kuraikkrom
EC_LEVELS = [
    ("H", qrcode.constants.ERROR_CORRECT_H),
    ("Q", qrcode.constants.ERROR_CORRECT_Q),
    ("M", qrcode.constants.ERROR_CORRECT_M),
    ("L", qrcode.constants.ERROR_CORRECT_L),
]


@dataclass
class QrResult:
    payload_bytes: bytes
    payload_text: str | None  # utf-8 decode aana text (illa-na None)
    payload_type: str  # "upi" / "url" / "text" / "binary"
    ec_level_read: str | None  # upload panna QR-oda original EC level
    qr_count: int
    zxing_ok: bool
    opencv_ok: bool
    decoders_agree: bool
    img_w: int
    img_h: int
    best_ec_level: str | None  # payload-ku fit aagura highest EC level
    qr_version: int | None
    module_count: int | None
    sha256: str
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------
# Image variants: decode fail aana, vera vera maari try pannrom
# ---------------------------------------------------------------
def _make_variants(gray: np.ndarray) -> list[tuple[str, np.ndarray]]:
    h, w = gray.shape[:2]
    longest = max(h, w)
    pad = max(20, int(longest * 0.1))

    # Quiet zone illaadha QR-kum help pannum
    bordered = cv2.copyMakeBorder(gray, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)

    variants: list[tuple[str, np.ndarray]] = [
        ("original", gray),
        ("border", bordered),
    ]

    if longest < 600:  # chinna image-na perusaakkrom
        big = cv2.resize(bordered, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        variants.append(("upscale", big))

    if longest > 1400:  # romba periya image-na kuraikkrom
        s = 900 / longest
        small = cv2.resize(bordered, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        variants.append(("downscale", small))

    _, otsu = cv2.threshold(bordered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(("otsu", otsu))

    adaptive = cv2.adaptiveThreshold(
        bordered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    variants.append(("adaptive", adaptive))

    variants.append(("inverted", cv2.bitwise_not(bordered)))
    return variants


# ---------------------------------------------------------------
# ZXing
# ---------------------------------------------------------------
def _zxing_read(img: np.ndarray) -> list:
    kwargs = dict(formats=zxingcpp.BarcodeFormat.QRCode, try_rotate=True, try_downscale=True)
    try:
        results = zxingcpp.read_barcodes(img, try_invert=True, **kwargs)
    except TypeError:  # sila versions-la try_invert illa
        results = zxingcpp.read_barcodes(img, **kwargs)
    return [r for r in results if r.valid]


def _zxing_area(r) -> float:
    """QR-oda size (periya QR-a mudhalla edukka)."""
    try:
        p = r.position
        pts = [p.top_left, p.top_right, p.bottom_right, p.bottom_left]
        xs = [q.x for q in pts]
        ys = [q.y for q in pts]
        return float((max(xs) - min(xs)) * (max(ys) - min(ys)))
    except Exception:
        return 0.0


# ---------------------------------------------------------------
# OpenCV
# ---------------------------------------------------------------
def _opencv_read(variants: list[tuple[str, np.ndarray]]) -> str | None:
    detector = cv2.QRCodeDetector()
    for _, img in variants:
        try:
            text, _, _ = detector.detectAndDecode(img)
        except cv2.error:
            continue
        if text:
            return text
    return None


# ---------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------
def _payload_type(text: str | None) -> str:
    if text is None:
        return "binary"
    low = text.lower()
    if low.startswith("upi://pay"):
        return "upi"
    if low.startswith(("http://", "https://")):
        return "url"
    return "text"


def mask_vpa(vpa: str) -> str:
    """UPI ID-a mask pannum: ab***@okhdfc"""
    if "@" not in vpa:
        return vpa[:2] + "***"
    local, handle = vpa.split("@", 1)
    return f"{local[:2]}***@{handle}"


def parse_upi(text: str) -> dict:
    """upi://pay?pa=...&pn=...&am=... -> important fields."""
    q = parse_qs(urlparse(text).query)

    def first(key: str) -> str | None:
        v = q.get(key)
        return v[0] if v else None

    pa = first("pa")
    return {
        "payee_vpa_masked": mask_vpa(pa) if pa else None,
        "payee_name": first("pn"),
        "amount": first("am"),
        "currency": first("cu"),
        "has_note": first("tn") is not None,
    }


def _capacity(payload_bytes: bytes, payload_text: str | None):
    """Payload-ku Level H (illa-na kuraivaana level) fit aagudha nu real-a check pannum."""
    data = payload_text if payload_text is not None else payload_bytes
    for name, level in EC_LEVELS:
        qr = qrcode.QRCode(version=None, error_correction=level, border=4)
        qr.add_data(data)
        try:
            qr.make(fit=True)
        except (DataOverflowError, ValueError):
            continue
        return name, qr.version, qr.modules_count
    return None, None, None


# ---------------------------------------------------------------
# Main function
# ---------------------------------------------------------------
def decode_qr(bgr: np.ndarray) -> QrResult:
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY) if bgr.ndim == 3 else bgr
    variants = _make_variants(gray)

    # ZXing: ovvoru variant-layum try, mudhal success-la nikkum
    zx_results: list = []
    for _, img in variants:
        zx_results = _zxing_read(img)
        if zx_results:
            break

    cv_text = _opencv_read(variants)

    if not zx_results and cv_text is None:
        raise NoQrError(
            "QR code padikka mudiyala. QR clear-a, muzhusa theriyara image upload pannunga "
            "(blur illama, QR-a suththi konjam veliya idam vittu)."
        )

    warnings: list[str] = []
    ec_read = None

    if zx_results:
        best = max(zx_results, key=_zxing_area)
        raw = getattr(best, "bytes", None)
        payload_bytes = bytes(raw) if raw else best.text.encode("utf-8")
        ec = getattr(best, "ec_level", None)
        ec_read = str(ec) if ec else None
        qr_count = len(zx_results)
    else:
        payload_bytes = cv_text.encode("utf-8")
        qr_count = 1
        warnings.append("ZXing-la decode aagala, OpenCV-la mattum aachu.")

    try:
        payload_text: str | None = payload_bytes.decode("utf-8")
    except UnicodeDecodeError:
        payload_text = None

    zxing_ok = bool(zx_results)
    opencv_ok = cv_text is not None
    agree = zxing_ok and opencv_ok and cv_text.encode("utf-8") == payload_bytes

    if zxing_ok and not opencv_ok:
        warnings.append("OpenCV-la decode aagala (ZXing-la aachu). Step 8-la rendum thevai, so clear QR better.")
    if zxing_ok and opencv_ok and not agree:
        warnings.append("ZXing, OpenCV rendum vera vera payload kaattudhu. ZXing result use aagum.")
    if qr_count > 1:
        warnings.append(f"{qr_count} QR codes theriyudhu. Perusa irukkura QR mattum use aagum.")

    best_ec, version, modules = _capacity(payload_bytes, payload_text)
    if best_ec is None:
        warnings.append("Payload romba periyadhu, QR-la fit aagala.")
    elif best_ec != "H":
        warnings.append(
            f"Indha payload Level H-la fit aagala (max Level {best_ec}). Face details kammi aagalaam."
        )
    if version is not None and version > 10:
        warnings.append(
            f"QR payload neelam (version {version}). Modules romba chinna-a irukkum, face detail kammi."
        )

    return QrResult(
        payload_bytes=payload_bytes,
        payload_text=payload_text,
        payload_type=_payload_type(payload_text),
        ec_level_read=ec_read,
        qr_count=qr_count,
        zxing_ok=zxing_ok,
        opencv_ok=opencv_ok,
        decoders_agree=agree,
        img_w=w,
        img_h=h,
        best_ec_level=best_ec,
        qr_version=version,
        module_count=modules,
        sha256=hashlib.sha256(payload_bytes).hexdigest(),
        warnings=warnings,
    )
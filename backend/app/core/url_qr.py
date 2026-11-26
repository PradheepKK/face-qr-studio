# URL -> normal QR (black on white, Level H) + real ZXing verify.

from urllib.parse import urlparse

import cv2
import numpy as np
import qrcode
import zxingcpp
from qrcode.exceptions import DataOverflowError

MAX_URL_LEN = 500
BORDER = 4  # quiet zone (modules)


def validate_url(raw: str) -> str:
    url = raw.strip()
    if not url:
        raise ValueError("Please enter a URL.")
    if len(url) > MAX_URL_LEN:
        raise ValueError(f"The URL is too long (max {MAX_URL_LEN} characters).")
    if any(c.isspace() for c in url):
        raise ValueError("The URL cannot contain spaces.")
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise ValueError("The URL must start with http:// or https://, e.g. https://example.com")
    return url


def make_url_qr(url: str, size: int) -> tuple[np.ndarray, dict]:
    """Return: (BGR image size x size, info)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        border=BORDER,
    )
    qr.add_data(url)
    try:
        qr.make(fit=True)
    except (DataOverflowError, ValueError):
        raise ValueError("The URL is too long for a QR code. Please use a shorter link.")

    modules = np.array(qr.modules, dtype=bool)
    n = modules.shape[0]
    total = n + 2 * BORDER
    s = max(1, size // total)

    canvas = np.full((size, size, 3), 255, dtype=np.uint8)
    side = total * s
    off = (size - side) // 2 + BORDER * s
    big = np.repeat(np.repeat(modules, s, axis=0), s, axis=1)
    canvas[off : off + n * s, off : off + n * s][big] = 0

    info = {"version": qr.version, "modules": n, "ec_level": "H"}
    return canvas, info


def verify(img: np.ndarray, url: str) -> bool:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    results = [r for r in zxingcpp.read_barcodes(gray, formats=zxingcpp.BarcodeFormat.QRCode) if r.valid]
    if not results:
        return False
    return all(r.text == url for r in results)
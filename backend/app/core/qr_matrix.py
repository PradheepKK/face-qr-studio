# QR module matrix build pannum + protected (function) zones kandupidikkum.
# Payload bytes-a maathaama, version + mask pattern mattum choose pannrom.

from dataclasses import dataclass

import numpy as np
import qrcode
from qrcode import util

EC_MAP = {
    "H": qrcode.constants.ERROR_CORRECT_H,
    "Q": qrcode.constants.ERROR_CORRECT_Q,
    "M": qrcode.constants.ERROR_CORRECT_M,
    "L": qrcode.constants.ERROR_CORRECT_L,
}


@dataclass
class QrMatrix:
    version: int
    ec_level: str
    mask: int
    size: int
    dark: np.ndarray  # (size, size) bool, True = dark module
    function: np.ndarray  # (size, size) bool, True = protected module


def qr_size(version: int) -> int:
    return 17 + 4 * version


def function_mask(version: int) -> np.ndarray:
    """Maatha koodadha modules: finder, separator, timing, alignment, format, version info."""
    n = qr_size(version)
    m = np.zeros((n, n), dtype=bool)

    # 3 finder patterns + separators (8x8 each)
    m[0:8, 0:8] = True
    m[0:8, n - 8 : n] = True
    m[n - 8 : n, 0:8] = True

    # Format information (+ always-dark module)
    m[8, 0:9] = True
    m[0:9, 8] = True
    m[8, n - 8 : n] = True
    m[n - 8 : n, 8] = True

    # Timing patterns
    m[6, :] = True
    m[:, 6] = True

    # Alignment patterns (5x5), finder idathula skip
    pos = util.pattern_position(version)
    for r in pos:
        for c in pos:
            if (r < 8 and c < 8) or (r < 8 and c >= n - 8) or (r >= n - 8 and c < 8):
                continue
            m[r - 2 : r + 3, c - 2 : c + 3] = True

    # Version information (version 7+)
    if version >= 7:
        m[0:6, n - 11 : n - 8] = True
        m[n - 11 : n - 8, 0:6] = True

    return m


def build_matrix(payload: bytes, version: int, ec: str, mask: int) -> QrMatrix:
    """Payload-a fixed version + mask-la QR matrix-a maathum."""
    qr = qrcode.QRCode(
        version=version,
        error_correction=EC_MAP[ec],
        border=0,
        mask_pattern=mask,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    if qr.version != version:
        raise ValueError(f"Payload version {version}-la fit aagala (version {qr.version} thevai).")

    dark = np.array(qr.modules, dtype=bool)
    return QrMatrix(
        version=version,
        ec_level=ec,
        mask=mask,
        size=dark.shape[0],
        dark=dark,
        function=function_mask(version),
    )
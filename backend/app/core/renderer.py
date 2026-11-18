# MapPlan-a final high-resolution image-a render pannum.
# Dark = QR color, Light = background color. Center dot-a pixel-level-la fix pannrom.

import re

import numpy as np

from app.core.face_mapper import MapPlan

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def hex_to_bgr(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b, g, r)


def _lum(hex_color: str) -> float:
    b, g, r = hex_to_bgr(hex_color)
    out = []
    for v in (r, g, b):
        s = v / 255.0
        out.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def check_colors(qr_hex: str, bg_hex: str) -> None:
    """Scan-ku mukkiyam: QR color dark-a, contrast nalla irukkanum."""
    if not HEX_RE.match(qr_hex) or not HEX_RE.match(bg_hex):
        raise ValueError("Color format thappu. Example: #000000")
    l1, l2 = _lum(qr_hex), _lum(bg_hex)
    if l1 >= l2:
        raise ValueError("QR color, background-a vida dark-a irukkanum.")
    ratio = (l2 + 0.05) / (l1 + 0.05)
    if ratio < 3.0:
        raise ValueError(f"Color contrast kammi ({ratio:.1f}:1). Kurainjadhu 3:1 venum.")


def render(plan: MapPlan, qr_hex: str, bg_hex: str, resolution: int) -> np.ndarray:
    """Return: BGR image (resolution x resolution)."""
    check_colors(qr_hex, bg_hex)

    total, border = plan.total, plan.border
    s = (resolution // total) // 3 * 3  # module pixel size (3-oda multiple)
    if s < 6:
        raise ValueError("Payload romba neelam, indha resolution-la modules romba chinna aagudhu. Perusa resolution select pannunga.")
    sub = s // 3

    # Halftone sub-cells -> pixels
    light = np.repeat(np.repeat(plan.light_sub, sub, axis=0), sub, axis=1)

    # Module-level dark map (quiet zone-oda)
    mod_dark = np.zeros((total, total), dtype=bool)
    n = plan.matrix.size
    mod_dark[border : border + n, border : border + n] = plan.matrix.dark

    # Center dot: ovvoru module-oda nadula QR bit-a force pannrom
    cs = max(sub, int(round(s * plan.center_frac)))
    if (s - cs) % 2:
        cs += 1
    o = (s - cs) // 2
    base = np.zeros((s, s), dtype=bool)
    base[o : o + cs, o : o + cs] = True
    cmask = np.tile(base, (total, total))
    dpx = np.repeat(np.repeat(mod_dark, s, axis=0), s, axis=1)
    light = np.where(cmask, ~dpx, light)

    # Colors apply
    qr_bgr = np.array(hex_to_bgr(qr_hex), dtype=np.uint8)
    bg_bgr = np.array(hex_to_bgr(bg_hex), dtype=np.uint8)

    side = total * s
    img = np.empty((side, side, 3), dtype=np.uint8)
    img[:] = bg_bgr
    img[~light] = qr_bgr

    # Exact resolution-ku center-la vaikkrom (padding = background color)
    canvas = np.empty((resolution, resolution, 3), dtype=np.uint8)
    canvas[:] = bg_bgr
    off = (resolution - side) // 2
    canvas[off : off + side, off : off + side] = img
    return canvas
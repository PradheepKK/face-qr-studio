# Style 1: Halftone Block renderer.
# Photo tone -> clustered dot (area modulated). Center sub-square = QR bit force.
# Background = normal solid QR modules. Function patterns = always solid.

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.core.face_detect import FaceResult
from app.core.face_mapper import choose_mask, head_crop, subject_mask
from app.core.qr_matrix import QrMatrix, qr_size

WORK_HI = 512  # tone map-oda working size
BORDER = 4  # quiet zone (modules)
BAND_ROWS = 6  # memory save panna module rows-a band-a process pannrom
HT_THRESHOLD = 0.30  # subject coverage idha vida adhigam na halftone cell


@dataclass
class HalftonePrep:
    tone: np.ndarray  # (WORK_HI, WORK_HI) float32, 1 = light, 0 = dark
    soft: np.ndarray  # (WORK_HI, WORK_HI) float32 subject mask 0..1
    segmentation: str


@dataclass
class HalftonePlan:
    matrix: QrMatrix
    version: int
    center_frac: float
    blend: float
    segmentation: str
    mask_costs: list[float] = field(default_factory=list)


# ---------------------------------------------------------------
# 1. Prepare: crop + segmentation + tone (version-ku independent, oru thadavai mattum)
# ---------------------------------------------------------------
def prepare(bgr: np.ndarray, face: FaceResult) -> HalftonePrep:
    crop, ox0, oy0, side = head_crop(bgr, face)
    interp = cv2.INTER_AREA if side >= WORK_HI else cv2.INTER_CUBIC
    small = cv2.resize(crop, (WORK_HI, WORK_HI), interpolation=interp)

    scale = WORK_HI / float(side)
    oval_s = ((face.oval.astype(np.float32) - np.array([ox0, oy0], np.float32)) * scale).astype(np.int32)

    soft, seg = subject_mask(small, oval_s)

    # Luminance + local contrast
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    eq = clahe.apply(gray)
    g = (0.5 * gray.astype(np.float32) + 0.5 * eq.astype(np.float32)) / 255.0

    # Sharpen: kann, eyebrow, mustache edges clear-a theriya
    blur = cv2.GaussianBlur(g, (0, 0), 2.5)
    g = np.clip(g + 0.6 * (g - blur), 0.0, 1.0)

    # Levels: hair dark-a, skin high-key (light)-a varanum (reference maari)
    inside = soft > 0.5
    lo = float(np.percentile(g[inside], 3)) if inside.sum() > 100 else 0.0

    oval_mask = np.zeros((WORK_HI, WORK_HI), np.uint8)
    cv2.fillPoly(oval_mask, [oval_s], 255)
    oval_mask = cv2.erode(oval_mask, np.ones((9, 9), np.uint8))
    skin = g[oval_mask > 0]
    med = float(np.median(skin)) if skin.size > 100 else 0.6

    span = max(0.15, med - lo)
    g = np.clip((g - lo) / span * 0.85, 0.0, 1.0)

    # Subject veliya = light (module level-la plain QR varum)
    tone = soft * g + (1.0 - soft) * 1.0
    return HalftonePrep(tone=tone.astype(np.float32), soft=soft.astype(np.float32), segmentation=seg)


# ---------------------------------------------------------------
# 2. Render
# ---------------------------------------------------------------
def render_halftone(
    prep: HalftonePrep,
    payload: bytes,
    ec: str,
    version: int,
    center_frac: float,
    blend: float,
    resolution: int,
    qm_cache: dict | None = None,
) -> tuple[np.ndarray, HalftonePlan]:
    """Return: (BGR image resolution x resolution, plan). Black on white."""
    n = qr_size(version)
    total = n + 2 * BORDER
    s = resolution // total  # oru module-oda pixel size
    if s < 8:
        raise ValueError(
            "Payload neelam, indha resolution-la modules romba chinna aagudhu. Perusa resolution select pannunga."
        )

    # Module-level target + best mask
    tone_mod = cv2.resize(prep.tone, (n, n), interpolation=cv2.INTER_AREA)
    soft_mod = cv2.resize(prep.soft, (n, n), interpolation=cv2.INTER_AREA)

    costs: list[float] = []
    if qm_cache is not None and version in qm_cache:
        qm = qm_cache[version]
    else:
        target_dark = 1.0 - tone_mod
        weight = 0.05 + 3.0 * soft_mod  # background-a mask choice-la ignore pannrom
        qm, costs = choose_mask(payload, version, ec, target_dark, weight)
        if qm_cache is not None:
            qm_cache[version] = qm

    bits = qm.dark  # (n, n) True = dark module
    mod_ht = (soft_mod > HT_THRESHOLD) & (~qm.function)  # halftone cells

    # High-res tone map (module grid-ku exact size)
    big = n * s
    tone_hi = cv2.resize(prep.tone, (big, big), interpolation=cv2.INTER_CUBIC)
    np.clip(tone_hi, 0.0, 1.0, out=tone_hi)

    # Cell template: clustered dot threshold (centre-la irundhu square-a valarum)
    c = (np.arange(s) + 0.5) / s * 2.0 - 1.0
    cheb = np.maximum(np.abs(c)[:, None], np.abs(c)[None, :])
    thr = (cheb**2).astype(np.float32)  # area fraction = r^2

    # Center square: QR bit force pannura idam
    cs = int(round(s * center_frac))
    cs = max(2, min(s, cs))
    if (s - cs) % 2:
        cs = cs + 1 if cs < s else cs - 1
    o = (s - cs) // 2
    cmask = np.zeros((s, s), dtype=bool)
    cmask[o : o + cs, o : o + cs] = True

    # Canvas: white
    canvas = np.full((resolution, resolution, 3), 255, dtype=np.uint8)
    off = (resolution - total * s) // 2 + BORDER * s

    for r0 in range(0, n, BAND_ROWS):
        r1 = min(n, r0 + BAND_ROWS)
        rows = r1 - r0

        bit_px = np.repeat(np.repeat(bits[r0:r1], s, axis=0), s, axis=1)
        ht_px = np.repeat(np.repeat(mod_ht[r0:r1], s, axis=0), s, axis=1)

        darkness = 1.0 - tone_hi[r0 * s : r1 * s, :]
        if blend > 0:
            darkness = (1.0 - blend) * darkness + blend * bit_px.astype(np.float32)

        dark = darkness > np.tile(thr, (rows, n))  # halftone dot
        dark = np.where(np.tile(cmask, (rows, n)), bit_px, dark)  # center = QR bit
        dark = np.where(ht_px, dark, bit_px)  # halftone illaadha cells = solid QR module

        y0 = off + r0 * s
        region = canvas[y0 : y0 + rows * s, off : off + big]
        region[dark] = 0

    plan = HalftonePlan(
        matrix=qm,
        version=version,
        center_frac=float(cs) / s,
        blend=blend,
        segmentation=prep.segmentation,
        mask_costs=costs,
    )
    return canvas, plan
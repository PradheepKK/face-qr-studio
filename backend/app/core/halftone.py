# Style 1: Halftone Block renderer (v2).
# - Mid-tone skin dots, pixel-level feature layer (kann/mukku/mustache sharp)
# - Alignment patterns face-kulla irundha halftone cell-a maarum (option)
# - Center sub-square = QR bit force

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.core.face_detect import FaceResult
from app.core.face_mapper import choose_mask, head_crop, subject_mask
from app.core.qr_matrix import QrMatrix, align_mask, qr_size

WORK_HI = 512
BORDER = 4
BAND_ROWS = 6
HT_THRESHOLD = 0.30  # subject coverage idha vida adhigam na halftone cell
FEATURE_T = 0.30  # idha vida dark pixel = solid black feature
SKIN_LEVEL = 0.55  # skin median tone (kuraiya = dots perusu)
CROP_SCALE = 1.6  # head crop (kuraiya = face perusa theriyum)


@dataclass
class HalftonePrep:
    tone: np.ndarray
    soft: np.ndarray
    segmentation: str


@dataclass
class HalftonePlan:
    matrix: QrMatrix
    version: int
    center_frac: float
    blend: float
    segmentation: str
    align_free: bool = False
    mask_costs: list[float] = field(default_factory=list)


def prepare(bgr: np.ndarray, face: FaceResult) -> HalftonePrep:
    crop, ox0, oy0, side = head_crop(bgr, face, CROP_SCALE)
    interp = cv2.INTER_AREA if side >= WORK_HI else cv2.INTER_CUBIC
    small = cv2.resize(crop, (WORK_HI, WORK_HI), interpolation=interp)

    scale = WORK_HI / float(side)
    oval_s = ((face.oval.astype(np.float32) - np.array([ox0, oy0], np.float32)) * scale).astype(np.int32)

    soft, seg = subject_mask(small, oval_s)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    eq = clahe.apply(gray)
    g = (0.4 * gray.astype(np.float32) + 0.6 * eq.astype(np.float32)) / 255.0

    # Sharpen: kann, eyebrow, mustache edges
    blur = cv2.GaussianBlur(g, (0, 0), 2.0)
    g = np.clip(g + 0.8 * (g - blur), 0.0, 1.0)

    inside = soft > 0.5
    lo = float(np.percentile(g[inside], 2)) if inside.sum() > 100 else 0.0

    oval_mask = np.zeros((WORK_HI, WORK_HI), np.uint8)
    cv2.fillPoly(oval_mask, [oval_s], 255)
    oval_mask = cv2.erode(oval_mask, np.ones((9, 9), np.uint8))
    skin = g[oval_mask > 0]
    med = float(np.median(skin)) if skin.size > 100 else 0.6

    span = max(0.15, med - lo)
    g = np.clip((g - lo) / span * SKIN_LEVEL, 0.0, 1.0)

    tone = soft * g + (1.0 - soft) * 1.0
    return HalftonePrep(tone=tone.astype(np.float32), soft=soft.astype(np.float32), segmentation=seg)


def render_halftone(
    prep: HalftonePrep,
    payload: bytes,
    ec: str,
    version: int,
    center_frac: float,
    blend: float,
    resolution: int,
    qm_cache: dict | None = None,
    align_free: bool = True,
) -> tuple[np.ndarray, HalftonePlan]:
    n = qr_size(version)
    total = n + 2 * BORDER
    s = resolution // total
    if s < 8:
        raise ValueError(
            "Payload neelam, indha resolution-la modules romba chinna aagudhu. Perusa resolution select pannunga."
        )

    tone_mod = cv2.resize(prep.tone, (n, n), interpolation=cv2.INTER_AREA)
    soft_mod = cv2.resize(prep.soft, (n, n), interpolation=cv2.INTER_AREA)

    costs: list[float] = []
    if qm_cache is not None and version in qm_cache:
        qm = qm_cache[version]
    else:
        target_dark = 1.0 - tone_mod
        weight = 0.05 + 3.0 * soft_mod
        qm, costs = choose_mask(payload, version, ec, target_dark, weight)
        if qm_cache is not None:
            qm_cache[version] = qm

    bits = qm.dark
    protected = qm.function.copy()
    if align_free:
        protected &= ~align_mask(version)  # alignment patterns face-kulla halftone aagum
    mod_ht = (soft_mod > HT_THRESHOLD) & (~protected)

    big = n * s
    tone_hi = cv2.resize(prep.tone, (big, big), interpolation=cv2.INTER_CUBIC)
    np.clip(tone_hi, 0.0, 1.0, out=tone_hi)

    cs = int(round(s * center_frac))
    cs = max(2, min(s, cs))
    if (s - cs) % 2:
        cs = cs + 1 if cs < s else cs - 1
    o = (s - cs) // 2
    cmask = np.zeros((s, s), dtype=bool)
    cmask[o : o + cs, o : o + cs] = True

    # Ring dot threshold: center square-oda edge-la irundhu veliya nokki valarum.
    # Center-ku ulla QR bit-a dots thodaadhu (decoder clear-a padikkum).
    c = (np.arange(s) + 0.5) / s * 2.0 - 1.0
    cheb = np.maximum(np.abs(c)[:, None], np.abs(c)[None, :])
    cf = cs / float(s)
    ring = np.clip((cheb - cf) / max(1e-3, 1.0 - cf), 0.0, 1.0)
    thr = (ring**1.5).astype(np.float32)

    canvas = np.full((resolution, resolution, 3), 255, dtype=np.uint8)
    off = (resolution - total * s) // 2 + BORDER * s

    for r0 in range(0, n, BAND_ROWS):
        r1 = min(n, r0 + BAND_ROWS)
        rows = r1 - r0

        bit_px = np.repeat(np.repeat(bits[r0:r1], s, axis=0), s, axis=1)
        ht_px = np.repeat(np.repeat(mod_ht[r0:r1], s, axis=0), s, axis=1)

        tone_band = tone_hi[r0 * s : r1 * s, :]
        darkness = 1.0 - tone_band
        if blend > 0:
            darkness = (1.0 - blend) * darkness + blend * bit_px.astype(np.float32)

        dot = darkness >= np.tile(thr, (rows, n)) * 0.999  # ring halftone dot
        feature = tone_band < FEATURE_T  # pixel-level sharp features
        dark = dot | feature
        dark = np.where(np.tile(cmask, (rows, n)), bit_px, dark)  # center = QR bit
        dark = np.where(ht_px, dark, bit_px)  # halftone illaadha = solid QR module

        y0 = off + r0 * s
        region = canvas[y0 : y0 + rows * s, off : off + big]
        region[dark] = 0

    plan = HalftonePlan(
        matrix=qm,
        version=version,
        center_frac=float(cs) / s,
        blend=blend,
        segmentation=prep.segmentation,
        align_free=align_free,
        mask_costs=costs,
    )
    return canvas, plan
# Style 1: Halftone Block renderer (v4).
# - Head + neck + shoulders crop
# - MediaPipe person segmentation (fallback: GrabCut)
# - Pure tone (no outline / line art): hair solid dark, skin dots, clothes real tone
# - Center sub-square = QR bit force

import threading
from dataclasses import dataclass, field

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from app.config import SEG_MODEL_PATH
from app.core.face_detect import FaceResult
from app.core.face_mapper import choose_mask
from app.core.qr_matrix import QrMatrix, align_mask, qr_size

WORK_HI = 512
BORDER = 4
BAND_ROWS = 6
HT_THRESHOLD = 0.18  # subject coverage idha vida adhigam na halftone cell
FEATURE_T = 0.33  # idha vida dark pixel = solid black
SKIN_LEVEL = 0.60  # adhigam = skin light, dots chinna
CROP_SCALE = 2.0  # head + shoulders (kuraiya = face perusa)
CROP_DOWN = 0.0  # crop keezha pogum (0 = hair top cut aagaadhu)


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


def _crop(bgr: np.ndarray, face: FaceResult):
    h, w = bgr.shape[:2]
    x, y, bw, bh = face.bbox
    side = max(64, int(round(CROP_SCALE * max(bw, bh))))
    cx = x + bw / 2
    cy = y + bh / 2 + CROP_DOWN * bh

    x0 = int(round(cx - side / 2))
    y0 = int(round(cy - side / 2))
    ox0, oy0 = x0, y0

    pad = max(0, -x0, -y0, x0 + side - w, y0 + side - h)
    src = bgr
    if pad > 0:
        src = cv2.copyMakeBorder(bgr, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        x0 += pad
        y0 += pad
    return src[y0 : y0 + side, x0 : x0 + side], ox0, oy0, side


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = np.zeros_like(mask)
    cv2.drawContours(out, cnts, -1, 255, -1)
    return out


# ---------------------------------------------------------------
# Segmentation 1: MediaPipe selfie segmenter
# ---------------------------------------------------------------
_segmenter = None
_seg_lock = threading.Lock()
_seg_failed = False


def _get_segmenter():
    global _segmenter, _seg_failed
    if _segmenter is None and not _seg_failed:
        try:
            if not SEG_MODEL_PATH.exists():
                raise FileNotFoundError(SEG_MODEL_PATH)
            opts = vision.ImageSegmenterOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(SEG_MODEL_PATH)),
                running_mode=vision.RunningMode.IMAGE,
                output_confidence_masks=True,
                output_category_mask=False,
            )
            _segmenter = vision.ImageSegmenter.create_from_options(opts)
        except Exception:
            _seg_failed = True
    return _segmenter


def _person_mask(small: np.ndarray, oval: np.ndarray):
    seg = _get_segmenter()
    if seg is None:
        return None
    try:
        rgb = np.ascontiguousarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        with _seg_lock:
            res = seg.segment(img)
        masks = res.confidence_masks
        m = masks[1] if len(masks) > 1 else masks[0]
        arr = np.squeeze(np.array(m.numpy_view(), dtype=np.float32))
        if arr.shape != small.shape[:2]:
            arr = cv2.resize(arr, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_LINEAR)

        # Orientation check: face center = person aaganum
        cx, cy = oval.mean(axis=0).astype(int)
        cx, cy = int(np.clip(cx, 0, arr.shape[1] - 1)), int(np.clip(cy, 0, arr.shape[0] - 1))
        if arr[cy, cx] < 0.5:
            arr = 1.0 - arr

        fg = ((arr > 0.5).astype(np.uint8)) * 255
        fg = cv2.medianBlur(fg, 5)
        face_m = np.zeros_like(fg)
        cv2.fillPoly(face_m, [oval], 255)
        fg = cv2.bitwise_or(fg, face_m)

        _, lab = cv2.connectedComponents(fg)
        c = lab[cy, cx]
        if c == 0:
            return None
        fg = ((lab == c).astype(np.uint8)) * 255
        fg = _fill_holes(fg)
        fg = cv2.dilate(fg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))  # hair strands

        ratio = float(fg.mean()) / 255.0
        if ratio < 0.10 or ratio > 0.92:
            return None
        return fg
    except Exception:
        return None


# ---------------------------------------------------------------
# Segmentation 2: GrabCut fallback
# ---------------------------------------------------------------
def _grabcut_subject(small: np.ndarray, gray: np.ndarray, oval: np.ndarray):
    size = small.shape[0]
    xs, ys = oval[:, 0], oval[:, 1]
    fw = float(xs.max() - xs.min())
    fh = float(ys.max() - ys.min())
    ox = float((xs.max() + xs.min()) / 2)
    oy = float((ys.max() + ys.min()) / 2)
    chin = float(ys.max())

    head = np.zeros((size, size), np.uint8)
    cv2.ellipse(head, (int(ox), int(oy - 0.30 * fh)), (int(0.85 * fw), int(0.88 * fh)), 0, 0, 360, 255, -1)
    body = np.zeros((size, size), np.uint8)
    cv2.rectangle(body, (int(ox - 0.30 * fw), int(oy)), (int(ox + 0.30 * fw), int(oy + 1.3 * fh)), 255, -1)
    cv2.ellipse(body, (int(ox), int(oy + 1.55 * fh)), (int(1.5 * fw), int(0.75 * fh)), 0, 0, 360, 255, -1)
    cv2.rectangle(body, (int(ox - 1.5 * fw), int(oy + 1.55 * fh)), (int(ox + 1.5 * fw), size), 255, -1)
    face_m = np.zeros((size, size), np.uint8)
    cv2.fillPoly(face_m, [oval], 255)
    prior = cv2.bitwise_or(cv2.bitwise_or(head, body), face_m)

    try:
        k = max(5, int(0.30 * fw)) | 1
        limit = cv2.dilate(prior, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        gc = np.full((size, size), cv2.GC_BGD, np.uint8)
        gc[limit > 0] = cv2.GC_PR_BGD
        gc[prior > 0] = cv2.GC_PR_FGD
        core = cv2.erode(face_m, np.ones((9, 9), np.uint8))
        gc[core > 0] = cv2.GC_FGD
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(small, gc, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
        fg = (((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)) * 255
    except Exception:
        return prior.copy()

    hair = (((gray < 76) & (head > 0)).astype(np.uint8)) * 255
    hair[int(chin):, :] = 0
    fg = cv2.bitwise_or(fg, hair)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    try:
        _, lab = cv2.connectedComponents(fg)
        c = lab[int(np.clip(oy, 0, size - 1)), int(np.clip(ox, 0, size - 1))]
        fg = ((lab == c).astype(np.uint8)) * 255
        fg = _fill_holes(fg)
        ratio = float(fg.mean()) / 255.0
        if c == 0 or ratio < 0.10 or ratio > 0.90:
            return prior.copy()
    except Exception:
        return prior.copy()
    return fg


# ---------------------------------------------------------------
# Prepare: tone (version-ku independent)
# ---------------------------------------------------------------
def prepare(bgr: np.ndarray, face: FaceResult) -> HalftonePrep:
    crop, ox0, oy0, side = _crop(bgr, face)
    interp = cv2.INTER_AREA if side >= WORK_HI else cv2.INTER_CUBIC
    small = cv2.resize(crop, (WORK_HI, WORK_HI), interpolation=interp)

    scale = WORK_HI / float(side)
    oval_s = ((face.oval.astype(np.float32) - np.array([ox0, oy0], np.float32)) * scale).astype(np.int32)
    oval_s = np.clip(oval_s, 0, WORK_HI - 1)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    fg = _person_mask(small, oval_s)
    if fg is not None:
        seg = "selfie-segmenter"
    else:
        fg = _grabcut_subject(small, gray, oval_s)
        seg = "grabcut-fallback"
    soft = cv2.GaussianBlur(fg, (0, 0), 1.5).astype(np.float32) / 255.0

        # Tone: face-kulla romba local contrast (lips, ear, eye theriya)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    g = (0.35 * gray.astype(np.float32) + 0.65 * eq.astype(np.float32)) / 255.0
    blur = cv2.GaussianBlur(g, (0, 0), 3.0)
    g = np.clip(g + 0.9 * (g - blur), 0.0, 1.0)  # ear, lip shape edges
    fine = cv2.GaussianBlur(g, (0, 0), 1.2)
    g = np.clip(g + 0.5 * (g - fine), 0.0, 1.0)  # fine details

    inside = soft > 0.5
    lo = float(np.percentile(g[inside], 2)) if inside.sum() > 100 else 0.0

    oval_mask = np.zeros((WORK_HI, WORK_HI), np.uint8)
    cv2.fillPoly(oval_mask, [oval_s], 255)
    oval_mask = cv2.erode(oval_mask, np.ones((9, 9), np.uint8))
    skin = g[oval_mask > 0]
    med = float(np.median(skin)) if skin.size > 100 else 0.6

    span = max(0.15, med - lo)
    g = np.clip((g - lo) / span * SKIN_LEVEL, 0.0, 1.0)

    # Hair, shirt dark-a (reference maari solid blocks)
    g = g * (1.0 - 0.5 * np.clip((0.5 - g) / 0.5, 0.0, 1.0))

    # Dark tones (hair, shirt) innum dark: reference maari solid blocks
    g = g * (1.0 - 0.6 * np.clip((0.5 - g) / 0.5, 0.0, 1.0))

    
    tone = soft * g + (1.0 - soft) * 1.0
    return HalftonePrep(tone=tone.astype(np.float32), soft=soft.astype(np.float32), segmentation=seg)


# ---------------------------------------------------------------
# Render
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
    align_free: bool = True,
) -> tuple[np.ndarray, HalftonePlan]:
    n = qr_size(version)
    total = n + 2 * BORDER
    s = resolution // total
    if s < 8:
        raise ValueError(
            "This QR holds a lot of data. Please choose a higher resolution."
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
        protected &= ~align_mask(version)
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

    c = (np.arange(s) + 0.5) / s * 2.0 - 1.0
    cheb = np.maximum(np.abs(c)[:, None], np.abs(c)[None, :])
    cf = cs / float(s)
    ring = np.clip((cheb - cf) / max(1e-3, 1.0 - cf), 0.0, 1.0)
    thr = (ring**0.9).astype(np.float32)

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

        dot = darkness >= np.tile(thr, (rows, n)) * 0.999
        feature = tone_band < FEATURE_T
        dark = dot | feature
        dark = np.where(np.tile(cmask, (rows, n)), bit_px, dark)
        dark = np.where(ht_px, dark, bit_px)

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
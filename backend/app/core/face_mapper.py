# CORE ALGORITHM: face photo -> QR modules mapping.
# Steps: head crop -> segmentation -> tone map -> mask choose -> constrained dither.

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.core.face_detect import FaceResult
from app.core.qr_matrix import QrMatrix, build_matrix, qr_size

WORK = 384  # processing size (speed-kaga)
BORDER = 4  # quiet zone (modules)
SUB = 3  # ovvoru module-um 3x3 sub-cells

# center = QR bit dot-oda base size (module-la evvalavu fraction)
STYLE_PRESETS = {
    "face": {"center": 0.45, "bg_strength": 1.0, "compress": False},
    "portrait": {"center": 0.50, "bg_strength": 0.55, "compress": False},
    "minimal": {"center": 0.65, "bg_strength": 1.0, "compress": True},
}


@dataclass
class MapPlan:
    matrix: QrMatrix
    light_sub: np.ndarray  # (3*total, 3*total) bool, True = light
    total: int  # modules incl. quiet zone
    border: int
    version: int
    center_frac: float
    mask_costs: list[float] = field(default_factory=list)
    segmentation: str = "grabcut"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def plan_version(min_version: int, density: int) -> int:
    """Density slider -> QR version (8..16). Payload-ku thevai minimum-kum keezha pogaadhu."""
    target = 8 + round(density / 100 * 8)
    return max(min_version, target)


# ---------------------------------------------------------------
# 1. Head crop (hair-um serthu)
# ---------------------------------------------------------------
def head_crop(bgr: np.ndarray, face: FaceResult, scale: float = 2.1, up: float = 0.26):
    h, w = bgr.shape[:2]
    x, y, bw, bh = face.bbox
    side = max(64, int(round(scale * max(bw, bh)))) 
    cx = x + bw / 2
    cy = y + bh / 2 - up * bh

    x0 = int(round(cx - side / 2))
    y0 = int(round(cy - side / 2))
    ox0, oy0 = x0, y0

    pad = max(0, -x0, -y0, x0 + side - w, y0 + side - h)
    src = bgr
    if pad > 0:
        src = cv2.copyMakeBorder(bgr, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        x0 += pad
        y0 += pad
    crop = src[y0 : y0 + side, x0 : x0 + side]
    return crop, ox0, oy0, side


# ---------------------------------------------------------------
# 2. Subject (head + hair) segmentation
# ---------------------------------------------------------------
def subject_mask(small: np.ndarray, oval: np.ndarray, torso: bool = False):
    size = small.shape[0]
    xs, ys = oval[:, 0], oval[:, 1]
    fw = float(xs.max() - xs.min())
    fh = float(ys.max() - ys.min())
    ox = float((xs.max() + xs.min()) / 2)
    oy = float((ys.max() + ys.min()) / 2)

    # Fallback: head ellipse + face oval
    ell = np.zeros((size, size), np.uint8)
    cv2.ellipse(ell, (int(ox), int(oy - 0.32 * fh)), (int(0.98 * fw), int(1.08 * fh)), 0, 0, 360, 255, -1)
    if torso:  # neck + shoulders
     cv2.ellipse(ell, (int(ox), int(oy + 1.55 * fh)), (int(1.5 * fw), int(0.95 * fh)), 0, 0, 360, 255, -1)
    fallback = ell.copy()
    cv2.fillPoly(fallback, [oval], 255)

    method = "grabcut"
    try:
        gc = np.full((size, size), cv2.GC_PR_BGD, np.uint8)
        gc[ell > 0] = cv2.GC_PR_FGD
        b = max(4, int(size * 0.04))
        gc[:b, :] = cv2.GC_BGD
        if not torso:
            gc[-b:, :] = cv2.GC_BGD
        gc[:, :b] = cv2.GC_BGD
        gc[:, -b:] = cv2.GC_BGD

        inner = np.zeros((size, size), np.uint8)
        cv2.fillPoly(inner, [oval], 1)
        inner = cv2.erode(inner, np.ones((5, 5), np.uint8))
        gc[inner > 0] = cv2.GC_FGD

        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(small, gc, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)

        fg = (((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)) * 255
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, k)

        # Face-oda connected part mattum
        _, lab = cv2.connectedComponents(fg)
        c = lab[int(oy), int(ox)]
        if c == 0:
            raise ValueError("face component illa")
        fg = ((lab == c).astype(np.uint8)) * 255

        # Holes fill
        cnts, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filled = np.zeros_like(fg)
        cv2.drawContours(filled, cnts, -1, 255, -1)
        fg = filled

        ratio = float(fg.mean()) / 255.0
        if ratio < 0.08 or ratio > 0.92:
            raise ValueError("segmentation reasonable illa")
    except Exception:
        fg = fallback
        method = "ellipse-fallback"

    soft = cv2.GaussianBlur(fg, (0, 0), 3).astype(np.float32) / 255.0
    return soft, method


# ---------------------------------------------------------------
# 3. Tone map (luminance + contrast)
# ---------------------------------------------------------------
def tone_map(small: np.ndarray, mask: np.ndarray, contrast: int, style: str) -> np.ndarray:
    p = STYLE_PRESETS[style]
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        eq = clahe.apply(gray)
    except Exception:
        eq = gray
    g = (0.5 * gray.astype(np.float32) + 0.5 * eq.astype(np.float32)) / 255.0

    wsum = float(mask.sum())
    m = float((g * mask).sum() / wsum) if wsum > 1 else float(g.mean())

    c = 0.7 + contrast / 100.0 * 1.1  # 0.7 .. 1.8
    g = (g - m) * c + (0.5 * m + 0.3)  # skin tone halftone-ku nalla range-la varum
    g = np.clip(g, 0.0, 1.0)

    if p["compress"]:  # minimal: subtle artwork
        g = 0.55 + 0.45 * g

    bg_tone = p["bg_strength"] + (1.0 - p["bg_strength"]) * (0.5 + 0.5 * g)
    out = mask * g + (1.0 - mask) * bg_tone
    return np.clip(out, 0.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------
# 4. Best mask pattern choose (face-oda match aagura mask)
# ---------------------------------------------------------------
def choose_mask(payload: bytes, version: int, ec: str, target_dark: np.ndarray, weight: np.ndarray):
    best = None
    costs: list[float] = []
    want_dark = target_dark >= 0.5
    for m in range(8):
        qm = build_matrix(payload, version, ec, m)
        data = ~qm.function
        mismatch = (qm.dark != want_dark) & data
        cost = float((np.abs(target_dark - 0.5) * weight * mismatch).sum())
        costs.append(round(cost, 2))
        if best is None or cost < best[0]:
            best = (cost, qm)
    return best[1], costs


# ---------------------------------------------------------------
# 5. Constrained Floyd-Steinberg dither
#    kind: 0 = free, 1 = forced (error diffuse illa), 2 = forced (error diffuse)
#    fval: forced cell light-a (True) / dark-a (False)
# ---------------------------------------------------------------
def dither_forced(g: np.ndarray, kind: np.ndarray, fval: np.ndarray) -> np.ndarray:
    h, w = g.shape
    buf = g.astype(np.float64).tolist()
    kd = kind.tolist()
    fv = fval.tolist()
    out = [[True] * w for _ in range(h)]

    for y in range(h):
        row, krow, frow, orow = buf[y], kd[y], fv[y], out[y]
        nxt = buf[y + 1] if y + 1 < h else None
        for x in range(w):
            old = row[x]
            k = krow[x]
            light = frow[x] if k else (old >= 0.5)
            orow[x] = light
            if k == 1:
                continue
            err = old - (1.0 if light else 0.0)
            if err > 1.0:
                err = 1.0
            elif err < -1.0:
                err = -1.0
            if x + 1 < w:
                row[x + 1] += err * 0.4375
            if nxt is not None:
                if x > 0:
                    nxt[x - 1] += err * 0.1875
                nxt[x] += err * 0.3125
                if x + 1 < w:
                    nxt[x + 1] += err * 0.0625
    return np.array(out, dtype=bool)


def _up(a: np.ndarray, n: int) -> np.ndarray:
    return np.repeat(np.repeat(a, n, axis=0), n, axis=1)


# ---------------------------------------------------------------
# Main: plan build
# ---------------------------------------------------------------
def build_plan(
    bgr: np.ndarray,
    face: FaceResult,
    payload: bytes,
    ec: str,
    min_version: int,
    style: str = "face",
    face_visibility: int = 70,
    density: int = 50,
    contrast: int = 50,
    center_frac: float | None = None,  # Step 8 retry-la override pannum
    version: int | None = None,  # Step 8 retry-la override pannum
) -> MapPlan:
    if style not in STYLE_PRESETS:
        raise ValueError(f"Theriyaadha style: {style}")
    preset = STYLE_PRESETS[style]

    v = version if version else plan_version(min_version, density)
    cf = center_frac if center_frac else clamp(preset["center"] - (face_visibility - 50) / 100.0 * 0.30, 0.34, 0.75)

    # Head crop + segmentation + tone
    crop, ox0, oy0, side = head_crop(bgr, face)
    small = cv2.resize(crop, (WORK, WORK), interpolation=cv2.INTER_AREA)
    scale = WORK / float(side)
    oval_s = ((face.oval.astype(np.float32) - np.array([ox0, oy0], np.float32)) * scale).astype(np.int32)

    soft, seg = subject_mask(small, oval_s)
    g = tone_map(small, soft, contrast, style)

    # Module grid-ku resize + sharpen
    n = qr_size(v)
    m_px = SUB * n
    g_sub = cv2.resize(g, (m_px, m_px), interpolation=cv2.INTER_AREA)
    s_sub = cv2.resize(soft, (m_px, m_px), interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(g_sub, (0, 0), 1.5)
    g_sub = np.clip(g_sub + 0.7 * (g_sub - blur), 0.0, 1.0)

    # Module-level target (1 = dark venum) + importance weight
    target_dark = 1.0 - g_sub.reshape(n, SUB, n, SUB).mean(axis=(1, 3))
    weight = 1.0 + 2.0 * s_sub.reshape(n, SUB, n, SUB).mean(axis=(1, 3))

    qm, costs = choose_mask(payload, v, ec, target_dark, weight)

    # Dither grid (quiet zone-oda)
    total = n + 2 * BORDER
    gsz = SUB * total
    off = SUB * BORDER

    g_full = np.ones((gsz, gsz), dtype=np.float32)
    g_full[off : off + m_px, off : off + m_px] = g_sub

    kind = np.ones((gsz, gsz), dtype=np.uint8)  # quiet zone: forced light
    fval = np.ones((gsz, gsz), dtype=bool)

    func_px = _up(qm.function, SUB)
    dark_px = _up(qm.dark, SUB)
    inner_kind = np.zeros((m_px, m_px), dtype=np.uint8)
    inner_val = np.ones((m_px, m_px), dtype=bool)

    inner_kind[func_px] = 1
    inner_val[func_px] = ~dark_px[func_px]

    rr, cc = np.nonzero(~qm.function)  # data modules
    inner_kind[rr * SUB + 1, cc * SUB + 1] = 2  # center sub-cell = QR bit
    inner_val[rr * SUB + 1, cc * SUB + 1] = ~qm.dark[rr, cc]

    kind[off : off + m_px, off : off + m_px] = inner_kind
    fval[off : off + m_px, off : off + m_px] = inner_val

    light_sub = dither_forced(g_full, kind, fval)

    return MapPlan(
        matrix=qm,
        light_sub=light_sub,
        total=total,
        border=BORDER,
        version=v,
        center_frac=float(cf),
        mask_costs=costs,
        segmentation=seg,
    )
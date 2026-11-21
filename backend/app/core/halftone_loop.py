# Halftone: render -> real validate (ZXing + OpenCV) -> fail na parameters adjust -> retry.

from typing import Callable

import numpy as np

from app.core.face_detect import FaceResult
from app.core.halftone import prepare, render_halftone
from app.core.retry_loop import Attempt, LoopResult
from app.core.validator import validate

MAX_ATTEMPTS = 7
BASE_VERSION = 10  # face detail-ku nalla balance


def _schedule(min_v: int) -> list[tuple[int, float, float]]:
    """(version, center dot size, QR-bit blend). Attempt-ku attempt scan-friendly aagum."""
    base = max(min_v, BASE_VERSION)
    raw = [
        (base, 0.36, 0.00),  # 1: reference style (face max)
        (base, 0.42, 0.10),
        (base, 0.48, 0.20),
        (max(min_v, base - 2), 0.48, 0.20),  # modules perusu
        (max(min_v, base - 2), 0.55, 0.32),
        (max(min_v, base - 3), 0.60, 0.42),
        (min_v, 0.66, 0.55),  # kadaisi muyarchi (face weak aagum)
    ]
    seen: set = set()
    out: list[tuple[int, float, float]] = []
    for v, c, b in raw:
        if (v, c, b) not in seen:
            seen.add((v, c, b))
            out.append((v, c, b))
    return out


def run_halftone_loop(
    person: np.ndarray,
    face: FaceResult,
    payload: bytes,
    ec: str,
    min_version: int,
    resolution: int,
    max_attempts: int = MAX_ATTEMPTS,
    progress: Callable[[int, int, str], None] | None = None,
) -> LoopResult:
    prep = prepare(person, face)  # segmentation + tone: oru thadavai
    schedule = _schedule(min_version)[:max_attempts]
    qm_cache: dict = {}

    attempts: list[Attempt] = []
    best = None  # (key, img, plan, report, no)
    last_error = "Render fail aachu."

    for idx, (ver, cen, blend) in enumerate(schedule):
        no = idx + 1
        att = Attempt(number=no, version=ver, center=cen)
        attempts.append(att)
        if progress:
            progress(no, len(schedule), f"Attempt {no}/{len(schedule)}: halftone render + scan test")

        try:
            img, plan = render_halftone(prep, payload, ec, ver, cen, blend, resolution, qm_cache)
        except ValueError as e:
            att.error = str(e)
            last_error = str(e)
            continue

        report = validate(img, payload)
        att.passed, att.total, att.verified = report.passed, report.total, report.verified

        key = (report.verified, report.required_passed, report.passed, -no)
        if best is None or key > best[0]:
            best = (key, img, plan, report, no)

        if report.verified:
            break

    if best is None:
        raise ValueError(last_error)

    _, img, plan, report, no = best
    if report.verified:
        if no == 1:
            msg = "Scan Verified: ZXing + OpenCV rendum payload exact-a padichchu."
        else:
            msg = (
                f"Scan Verified (attempt {no}). Scan aaga vendi face detail konjam kuraichom "
                f"(center dot perusu, QR strength adhigam, version {plan.version})."
            )
    else:
        msg = (
            f"Scan verify fail: {len(attempts)} attempts-lum required checks pass aagala. "
            f"Best result kaattrom, aana idhu scan aagum nu guarantee illa. "
            f"Perusa resolution use pannunga allathu QR payload kammi-a irukkura QR try pannunga."
        )

    return LoopResult(
        image=img, plan=plan, report=report, verified=report.verified,
        attempts=attempts, final_attempt=no, message=msg,
    )
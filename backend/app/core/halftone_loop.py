# Halftone: render -> real validate (ZXing required, OpenCV advisory)
# -> fail na parameters adjust -> retry.

from typing import Callable

import numpy as np

from app.core.face_detect import FaceResult
from app.core.halftone import prepare, render_halftone
from app.core.retry_loop import Attempt, LoopResult
from app.core.validator import validate

MAX_ATTEMPTS = 7
BASE_VERSION = 10  # perusa modules = clear face (reference maari)
def _schedule(min_v: int) -> list[tuple[int, float, float, bool]]:
    """(version, center dot, QR-bit blend, alignment patterns halftone-a?)"""
    base = max(min_v, BASE_VERSION)
    raw = [
        (base, 0.34, 0.04, True),
        (base, 0.40, 0.10, True),
        (base, 0.46, 0.18, False),
        (max(min_v, base - 2), 0.50, 0.24, False),
        (max(min_v, base - 3), 0.56, 0.34, False),
        (max(min_v, base - 4), 0.62, 0.44, False),
        (min_v, 0.68, 0.56, False),
    ]
    seen: set = set()
    out: list[tuple[int, float, float, bool]] = []
    for item in raw:
        if item not in seen:
            seen.add(item)
            out.append(item)
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

    for idx, (ver, cen, blend, afree) in enumerate(schedule):
        no = idx + 1
        att = Attempt(number=no, version=ver, center=cen)
        attempts.append(att)
        if progress:
            progress(no, len(schedule), f"Creating your Face QR ({no}/{len(schedule)})...")

        try:
            img, plan = render_halftone(
                prep, payload, ec, ver, cen, blend, resolution, qm_cache, afree
            )
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
            msg = "Scan Verified"
        else:
            msg = (
                f"Scan Verified (attempt ). We slightly reduced facial details to ensure better scanning reliability. "
                f"(Larger center dot, stronger QR pattern, version {plan.version})."
            )

        # OpenCV advisory: fail aanaalum "Verified" block aagadhu, aana user-ku therivikkrom
        if any(c.decoder == "opencv" and not c.ok for c in report.checks):
            msg += (
                "Note: OpenCV's basic detector cannot read this dense design (ZXing can). Scanning is not guaranteed to work on all phones. Please test it with your own phone."
            )
    else:
        msg = (
            f"Scan verification failed: The required checks did not pass in any of the  attempts. "
            f"We are showing the best available result, but scanning is not guaranteed to work. "
            f"Please use a higher resolution or try a QR code with a smaller payload."
        )

    return LoopResult(
        image=img, plan=plan, report=report, verified=report.verified,
        attempts=attempts, final_attempt=no, message=msg,
    )
# Generate -> validate -> fail aana parameters adjust pannitu thirumba try.
# Success aagara varai, allathu max attempts varai.

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from app.core.face_detect import FaceResult
from app.core.face_mapper import STYLE_PRESETS, build_plan, clamp, plan_version
from app.core.renderer import check_colors, render
from app.core.validator import ValidationReport, validate

MAX_ATTEMPTS = 7


@dataclass
class Attempt:
    number: int
    version: int
    center: float
    passed: int = 0
    total: int = 0
    verified: bool = False
    error: str | None = None

    def to_dict(self) -> dict:
        d = {"n": self.number, "v": self.version, "c": round(self.center, 2), "ok": self.verified}
        if self.error:
            d["err"] = self.error
        else:
            d["p"] = self.passed
            d["t"] = self.total
        return d


@dataclass
class LoopResult:
    image: np.ndarray
    plan: object  # MapPlan
    report: ValidationReport
    verified: bool
    attempts: list[Attempt] = field(default_factory=list)
    final_attempt: int = 1
    message: str = ""


def _schedule(base_v: int, base_c: float, min_v: int) -> list[tuple[int, float]]:
    """Attempt-ku attempt maatha vendiya (version, center dot size) list."""
    cap = 0.85
    raw = [
        (base_v, base_c),  # 1: user settings appadiye
        (base_v, base_c + 0.07),  # 2: center dot konjam perusu
        (base_v, base_c + 0.14),  # 3
        (max(min_v, base_v - 2), base_c + 0.14),  # 4: modules perusu
        (max(min_v, base_v - 4), base_c + 0.20),  # 5
        (max(min_v, base_v - 4), base_c + 0.30),  # 6
        (min_v, 0.80),  # 7: kadaisi muyarchi (face weak aagum)
    ]
    seen: set[tuple[int, float]] = set()
    out: list[tuple[int, float]] = []
    for v, c in raw:
        item = (v, round(min(cap, c), 3))
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def run_retry_loop(
    person: np.ndarray,
    face: FaceResult,
    payload: bytes,
    ec: str,
    min_version: int,
    style: str,
    face_visibility: int,
    density: int,
    contrast: int,
    qr_color: str,
    bg_color: str,
    resolution: int,
    max_attempts: int = MAX_ATTEMPTS,
    progress: Callable[[int, int, str], None] | None = None,
) -> LoopResult:
    if style not in STYLE_PRESETS:
        raise ValueError(f"Theriyaadha style: {style}")
    check_colors(qr_color, bg_color)  # color thappa irundha udane error (retry-la fix aagaadhu)

    # build_plan-la irukkura same formula (base values)
    base_v = plan_version(min_version, density)
    base_c = clamp(STYLE_PRESETS[style]["center"] - (face_visibility - 50) / 100.0 * 0.30, 0.34, 0.75)
    schedule = _schedule(base_v, base_c, min_version)[:max_attempts]

    attempts: list[Attempt] = []
    best = None  # (key, img, plan, report, attempt_no)
    last_error = "Render fail aachu."

    for idx, (ver, cen) in enumerate(schedule):
        no = idx + 1
        att = Attempt(number=no, version=ver, center=cen)
        attempts.append(att)
        if progress:
            progress(no, len(schedule), f"Attempt {no}/{len(schedule)}: generate + scan test")

        try:
            plan = build_plan(
                person, face, payload, ec, min_version,
                style=style, face_visibility=face_visibility, density=density,
                contrast=contrast, center_frac=cen, version=ver,
            )
            img = render(plan, qr_color, bg_color, resolution)
        except ValueError as e:
            att.error = str(e)
            last_error = str(e)
            continue

        report = validate(img, payload)
        att.passed, att.total, att.verified = report.passed, report.total, report.verified

        # verified > required pass count > total pass count > mudhal attempt (face adhigam theriyum)
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
                f"Scan Verified (attempt {no}). Scan aaga vendi face visibility konjam "
                f"kuraichom (center dot perusu, version {plan.version})."
            )
    else:
        msg = (
            f"Scan verify fail: {len(attempts)} attempts-lum required checks pass aagala. "
            f"Best result kaattrom, aana idhu scan aagum nu guarantee illa. "
            f"Payload neelama irundha, Face visibility kammi pannunga allathu perusa resolution use pannunga."
        )

    return LoopResult(
        image=img, plan=plan, report=report, verified=report.verified,
        attempts=attempts, final_attempt=no, message=msg,
    )
# Job endpoints:
#   POST /api/jobs              -> job_id (202)
#   GET  /api/jobs/{id}         -> progress + status
#   GET  /api/jobs/{id}/result  -> PNG (oru thadavai, apram job delete)

import logging
import threading
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.config import (
    ALLOWED_PERSON_TYPES,
    ALLOWED_QR_TYPES,
    MAX_IMAGE_SIDE,
    MAX_PERSON_MB,
    MAX_QR_MB,
)
from app.core.face_detect import ModelMissingError, NoFaceError, detect_face
from app.core.job_store import TooManyJobsError, store
from app.core.qr_decode import NoQrError, decode_qr
from app.core.renderer import check_colors
from app.core.retry_loop import run_retry_loop
from app.schemas.jobs import JobCreated, JobResultMeta, JobStatus
from app.utils.file_validation import read_validated_image
from app.utils.image_io import decode_image_bgr, encode_png

router = APIRouter(prefix="/api", tags=["jobs"])
logger = logging.getLogger("faceqr")

ALLOWED_RES = (1024, 2048, 4096)
# Endha styles-oda renderer ready. Step 11-la "halftone", Step 12-la "pixel" serkkalam.
BUILT_STYLES: set[str] = {"halftone"}
_slots = threading.Semaphore(2)  # max 2 jobs oru nerathula


def _run_job(job_id: str, person_bytes: bytes, qr_bytes: bytes, p: dict) -> None:
    """Background thread: full pipeline + real progress updates."""
    store.update(job_id, message="Queue-la wait pannrom...")
    with _slots:
        try:
            store.update(job_id, state="running", progress=5, message="Reading your photo...")
            person_bgr, _ = decode_image_bgr(person_bytes, max_side=MAX_IMAGE_SIDE)

            store.update(job_id, progress=12, message="Detecting your face...")
            face = detect_face(person_bgr)

            store.update(job_id, progress=22, message="Reading the payment QR...")
            qr_bgr, _ = decode_image_bgr(qr_bytes, max_side=MAX_IMAGE_SIDE)
            qr = decode_qr(qr_bgr)
            if qr.best_ec_level is None:
                raise ValueError("This QR contains too much data to build a Face QR.")

            def on_progress(no: int, total: int, msg: str) -> None:
                pct = 25 + int((no - 1) / max(1, total) * 70)
                store.update(job_id, progress=pct, attempt=no, total_attempts=total, message=msg)

            res = run_retry_loop(
                person_bgr,
                face,
                qr.payload_bytes,
                qr.best_ec_level,
                qr.qr_version,
                style=p["style"],
                face_visibility=p["face_visibility"],
                density=p["density"],
                contrast=p["contrast"],
                qr_color=p["qr_color"],
                bg_color=p["bg_color"],
                resolution=p["resolution"],
                progress=on_progress,
            )

            store.update(job_id, progress=97, message="Preparing your image...")
            png = encode_png(res.image)
            plan = res.plan
            meta = {
                "verified": res.verified,
                "summary": res.report.summary(),
                "message": res.message,
                "checks": [
                    {"decoder": c.decoder, "variant": c.variant, "ok": c.ok, "required": c.required}
                    for c in res.report.checks
                ],
                "attempts": [a.to_dict() for a in res.attempts],
                "final_attempt": res.final_attempt,
                "qr_version": plan.version,
                "mask": plan.matrix.mask,
                "ec_level": plan.matrix.ec_level,
                "center_frac": round(plan.center_frac, 2),
                "segmentation": plan.segmentation,
                "resolution": p["resolution"],
            }
            store.update(job_id, state="done", progress=100, message="Finishing up", meta=meta, png=png)

        except (NoFaceError, NoQrError) as e:
            store.update(job_id, state="error", error=str(e), error_status=422)
        except ModelMissingError as e:
            store.update(job_id, state="error", error=str(e), error_status=500)
        except ValueError as e:
            store.update(job_id, state="error", error=str(e), error_status=400)
        except Exception:
            logger.exception("Job fail aachu")  # payload log aagaadhu
            store.update(
                job_id,
                state="error",
                error="Something went wrong on the server. Please try again.",
                error_status=500,
            )


@router.post("/jobs", response_model=JobCreated, status_code=202)
async def create_job(
    person: UploadFile = File(...),
    qr: UploadFile = File(...),
    style: Literal["halftone"] = Form("halftone"),
    qr_color: str = Form("#000000"),
    bg_color: str = Form("#ffffff"),
    face_visibility: int = Form(70, ge=0, le=100),
    density: int = Form(50, ge=0, le=100),
    contrast: int = Form(50, ge=0, le=100),
    resolution: int = Form(2048),
):
    if style not in BUILT_STYLES:
        raise HTTPException(
            status_code=501,
            detail="This style is not available yet.",
        )
    try:
        check_colors(qr_color, bg_color)  # thappu color-na udane error
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    person_bytes = await read_validated_image(person, ALLOWED_PERSON_TYPES, MAX_PERSON_MB)
    qr_bytes = await read_validated_image(qr, ALLOWED_QR_TYPES, MAX_QR_MB)

    try:
        job_id = store.create()
    except TooManyJobsError:
        raise HTTPException(status_code=429, detail=" The server is busy. Please try again shortly.")

    params = dict(
        style=style,
        qr_color=qr_color,
        bg_color=bg_color,
        face_visibility=face_visibility,
        density=density,
        contrast=contrast,
        resolution=resolution,
    )
    threading.Thread(target=_run_job, args=(job_id, person_bytes, qr_bytes, params), daemon=True).start()
    return JobCreated(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    job = store.snapshot(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Request not found (it may have expired).")
    return JobStatus(
        job_id=job.id,
        state=job.state,
        progress=job.progress,
        message=job.message,
        attempt=job.attempt,
        total_attempts=job.total_attempts,
        error=job.error,
        error_status=job.error_status,
        result=JobResultMeta(**job.meta) if job.meta else None,
    )


@router.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    job = store.snapshot(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Request not found (it may have expired).")
    if job.state != "done":
        raise HTTPException(status_code=409, detail="The result is not ready yet.")
    png = store.pop_result(job_id)
    if png is None:
        raise HTTPException(status_code=404, detail="Result already download aachu.")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})
# POST /api/generate -> Face QR PNG + real scan validation status (retry loop-oda).

import json
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.config import (
    ALLOWED_PERSON_TYPES,
    ALLOWED_QR_TYPES,
    MAX_IMAGE_SIDE,
    MAX_PERSON_MB,
    MAX_QR_MB,
)
from app.core.face_detect import ModelMissingError, NoFaceError, detect_face
from app.core.qr_decode import NoQrError, decode_qr
from app.core.retry_loop import run_retry_loop
from app.utils.file_validation import read_validated_image
from app.utils.image_io import decode_image_bgr, encode_png

router = APIRouter(prefix="/api", tags=["generate"])

ALLOWED_RES = (1024, 2048, 4096)


def _ascii(text: str) -> str:
    """HTTP header-la ASCII mattum."""
    return text.encode("ascii", "ignore").decode("ascii")


def _work(person_bytes: bytes, qr_bytes: bytes, p: dict):
    person_bgr, _ = decode_image_bgr(person_bytes, max_side=MAX_IMAGE_SIDE)
    face = detect_face(person_bgr)

    qr_bgr, _ = decode_image_bgr(qr_bytes, max_side=MAX_IMAGE_SIDE)
    qr = decode_qr(qr_bgr)
    if qr.best_ec_level is None:
        raise ValueError("QR payload romba periyadhu, face QR-ku fit aagala.")

    result = run_retry_loop(
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
    )
    return encode_png(result.image), result, qr


@router.post("/generate")
async def generate(
    person: UploadFile = File(...),
    qr: UploadFile = File(...),
    style: Literal["face", "portrait", "minimal"] = Form("face"),
    qr_color: str = Form("#000000"),
    bg_color: str = Form("#ffffff"),
    face_visibility: int = Form(70, ge=0, le=100),
    density: int = Form(50, ge=0, le=100),
    contrast: int = Form(50, ge=0, le=100),
    resolution: int = Form(2048),
):
    if resolution not in ALLOWED_RES:
        raise HTTPException(status_code=400, detail=f"Resolution {ALLOWED_RES}-la onnu irukkanum.")

    person_bytes = await read_validated_image(person, ALLOWED_PERSON_TYPES, MAX_PERSON_MB)
    qr_bytes = await read_validated_image(qr, ALLOWED_QR_TYPES, MAX_QR_MB)

    params = dict(
        style=style,
        qr_color=qr_color,
        bg_color=bg_color,
        face_visibility=face_visibility,
        density=density,
        contrast=contrast,
        resolution=resolution,
    )

    try:
        png, res, qr_res = await run_in_threadpool(_work, person_bytes, qr_bytes, params)
    except (NoFaceError, NoQrError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ModelMissingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Photos memory-la irundhu vidurom (disk-la store aagala)
        del person_bytes, qr_bytes

    plan = res.plan
    headers = {
        "X-Scan-Verified": "verified" if res.verified else "failed",
        "X-Validation-Summary": res.report.summary(),
        "X-Validation-Checks": res.report.detail(),
        "X-Validation-Message": _ascii(res.message),
        "X-Attempts": str(len(res.attempts)),
        "X-Final-Attempt": str(res.final_attempt),
        "X-Attempt-Log": json.dumps([a.to_dict() for a in res.attempts], separators=(",", ":")),
        "X-QR-Version": str(plan.version),
        "X-QR-Mask": str(plan.matrix.mask),
        "X-QR-EC-Level": plan.matrix.ec_level,
        "X-Center-Frac": f"{plan.center_frac:.2f}",
        "X-Segmentation": plan.segmentation,
        "X-Payload-SHA256": qr_res.sha256,
    }
    return Response(content=png, media_type="image/png", headers=headers)
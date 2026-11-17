# Face endpoints:
#   POST /api/face/detect   -> face info JSON
#   POST /api/face/preview  -> face box + oval varanja PNG (test-kaga)

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.config import ALLOWED_PERSON_TYPES, MAX_IMAGE_SIDE, MAX_PERSON_MB
from app.core.face_detect import (
    FaceResult,
    ModelMissingError,
    NoFaceError,
    detect_face,
    draw_preview,
)
from app.schemas.models import BBox, FaceDetectResponse
from app.utils.file_validation import read_validated_image
from app.utils.image_io import decode_image_bgr, encode_png

router = APIRouter(prefix="/api/face", tags=["face"])


def _process(data: bytes):
    """Bytes -> image -> face detect. Idhu thread-la run aagum (server block aagaadhu)."""
    bgr, downscaled = decode_image_bgr(data, max_side=MAX_IMAGE_SIDE)
    result = detect_face(bgr)
    return bgr, downscaled, result


async def _run(file: UploadFile):
    data = await read_validated_image(file, ALLOWED_PERSON_TYPES, MAX_PERSON_MB)
    try:
        return await run_in_threadpool(_process, data)
    except NoFaceError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ModelMissingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Photo bytes-a memory-la irundhu vidurom (disk-la store aagala)
        del data


@router.post("/detect", response_model=FaceDetectResponse)
async def detect(file: UploadFile = File(...)):
    _, downscaled, r = await _run(file)
    x, y, w, h = r.bbox
    return FaceDetectResponse(
        ok=len(r.warnings) == 0,
        face_count=r.face_count,
        image_width=r.img_w,
        image_height=r.img_h,
        downscaled=downscaled,
        bbox=BBox(x=x, y=y, width=w, height=h),
        face_area_ratio=r.area_ratio,
        landmark_count=len(r.landmarks),
        sharpness=r.sharpness,
        brightness=r.brightness,
        warnings=r.warnings,
    )


@router.post("/preview")
async def preview(file: UploadFile = File(...)):
    bgr, _, r = await _run(file)
    png = await run_in_threadpool(lambda: encode_png(draw_preview(bgr, r)))
    return Response(content=png, media_type="image/png")
# QR endpoint:
#   POST /api/qr/decode -> payload info (masked). Full payload response-la varaadhu.

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import ALLOWED_QR_TYPES, MAX_IMAGE_SIDE, MAX_QR_MB
from app.core.qr_decode import NoQrError, decode_qr, parse_upi
from app.schemas.models import DecoderStatus, QrDecodeResponse, UpiInfo
from app.utils.file_validation import read_validated_image
from app.utils.image_io import decode_image_bgr

from fastapi.responses import Response

from app.core.url_qr import make_url_qr, validate_url, verify
from app.schemas.models import UrlQrRequest
from app.utils.image_io import encode_png

router = APIRouter(prefix="/api/qr", tags=["qr"])


def _process(data: bytes):
    """Bytes -> image -> QR decode. Thread-la run aagum."""
    bgr, _ = decode_image_bgr(data, max_side=MAX_IMAGE_SIDE)
    return decode_qr(bgr)


@router.post("/decode", response_model=QrDecodeResponse)
async def decode(file: UploadFile = File(...)):
    data = await read_validated_image(file, ALLOWED_QR_TYPES, MAX_QR_MB)
    try:
        r = await run_in_threadpool(_process, data)
    except NoQrError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Image bytes-a memory-la irundhu vidurom (disk-la store aagala)
        del data

    text = r.payload_text
    preview = (text[:10] + "…") if text and len(text) > 10 else (text or "<binary>")
    upi = UpiInfo(**parse_upi(text)) if r.payload_type == "upi" and text else None

    return QrDecodeResponse(
        ok=r.best_ec_level is not None,
        payload_type=r.payload_type,
        payload_length=len(r.payload_bytes),
        payload_preview=preview,
        payload_sha256=r.sha256,
        decoders=DecoderStatus(zxing=r.zxing_ok, opencv=r.opencv_ok, agree=r.decoders_agree),
        qr_count=r.qr_count,
        original_ec_level=r.ec_level_read,
        best_ec_level=r.best_ec_level,
        level_h_possible=r.best_ec_level == "H",
        qr_version=r.qr_version,
        module_count=r.module_count,
        image_width=r.img_w,
        image_height=r.img_h,
        upi=upi,
        warnings=r.warnings,
    )

    

ALLOWED_SIZES = (512, 1024, 2048)
@router.post("/generate")
async def generate_url_qr(body: UrlQrRequest):
    if body.size not in ALLOWED_SIZES:
        raise HTTPException(status_code=400, detail=f"Size {ALLOWED_SIZES}-la onnu irukkanum.")
    try:
        url = validate_url(body.url)
        img, info = await run_in_threadpool(make_url_qr, url, body.size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    verified = await run_in_threadpool(verify, img, url)
    png = encode_png(img)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-QR-Verified": "verified" if verified else "failed",
            "X-QR-Version": str(info["version"]),
            "X-QR-Modules": str(info["modules"]),
            "X-QR-EC-Level": info["ec_level"],
        },
    )
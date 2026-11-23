
# API response formats (Pydantic).

from pydantic import BaseModel


class BBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class FaceDetectResponse(BaseModel):
    ok: bool
    face_count: int
    image_width: int
    image_height: int
    downscaled: bool
    bbox: BBox
    face_area_ratio: float
    landmark_count: int
    sharpness: float
    brightness: float
    warnings: list[str]


class UpiInfo(BaseModel):
    payee_vpa_masked: str | None
    payee_name: str | None
    amount: str | None
    currency: str | None
    has_note: bool


class DecoderStatus(BaseModel):
    zxing: bool
    opencv: bool
    agree: bool


class QrDecodeResponse(BaseModel):
    ok: bool
    payload_type: str
    payload_length: int
    payload_preview: str
    payload_sha256: str
    decoders: DecoderStatus
    qr_count: int
    original_ec_level: str | None
    best_ec_level: str | None
    level_h_possible: bool
    qr_version: int | None
    module_count: int | None
    image_width: int
    image_height: int
    upi: UpiInfo | None
    warnings: list[str]


# URL QR generation request
class UrlQrRequest(BaseModel):
    url: str
    size: int = 1024  # 512 / 1024 / 2048

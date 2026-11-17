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
    image_width: int  # processing-ku use panna image size
    image_height: int
    downscaled: bool  # periya image-a kuraichomaa
    bbox: BBox
    face_area_ratio: float  # face, image-la evvalavu % (0-1)
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
    agree: bool  # rendum same payload-a kodutthucha


class QrDecodeResponse(BaseModel):
    ok: bool
    payload_type: str  # upi / url / text / binary
    payload_length: int  # bytes
    payload_preview: str  # first 10 chars mattum (masked)
    payload_sha256: str  # exact compare-kaga hash
    decoders: DecoderStatus
    qr_count: int
    original_ec_level: str | None
    best_ec_level: str | None  # payload-ku fit aagura highest level
    level_h_possible: bool
    qr_version: int | None
    module_count: int | None
    image_width: int
    image_height: int
    upi: UpiInfo | None
    warnings: list[str]
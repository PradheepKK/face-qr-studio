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
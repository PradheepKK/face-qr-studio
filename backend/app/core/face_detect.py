# MediaPipe Face Landmarker vachu face detect pannum.
# 478 landmarks, face box, face oval (mask) ellaam kudukkum.

import threading
from dataclasses import dataclass, field

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from app.config import FACE_LANDMARKER_PATH, MIN_FACE_AREA_RATIO

# Face oval-oda landmark indices (order-la, mask poda use aagum)
FACE_OVAL = [
    10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
    397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
    172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109,
]


class NoFaceError(Exception):
    """Image-la face kandupidikka mudiyala."""


class ModelMissingError(Exception):
    """face_landmarker.task model file illa."""


@dataclass
class FaceResult:
    face_count: int
    img_w: int
    img_h: int
    landmarks: np.ndarray  # (478, 2) pixel coordinates
    oval: np.ndarray  # (36, 2) int32 face oval polygon
    bbox: tuple[int, int, int, int]  # x, y, w, h
    sharpness: float
    brightness: float
    area_ratio: float
    warnings: list[str] = field(default_factory=list)


# Landmarker-a oru thadavai mattum load pannrom (thirumba thirumba load panna slow)
_landmarker = None
_lock = threading.Lock()


def _get_landmarker():
    global _landmarker
    if _landmarker is None:
        if not FACE_LANDMARKER_PATH.exists():
            raise ModelMissingError(
                "Face model is missing on the server. python scripts\\download_models.py"
            )
        options = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(FACE_LANDMARKER_PATH)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=5,  # pala face irundha kandupidikka
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
        )
        _landmarker = vision.FaceLandmarker.create_from_options(options)
    return _landmarker


def detect_face(bgr: np.ndarray) -> FaceResult:
    """Image-la perusa irukkura face-a kandupidikkum. Face illa-na NoFaceError."""
    h, w = bgr.shape[:2]
    rgb = np.ascontiguousarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # Landmarker thread-safe illa, adhunaala lock
    with _lock:
        result = _get_landmarker().detect(mp_image)

    faces = result.face_landmarks
    if not faces:
        raise NoFaceError("No face found in the photo. Please upload a clear, front-facing photo with good lighting.")

    # Pala face irundha, perusa irukkura face-a edukkrom
    best_pts = None
    best_area = -1.0
    for lm in faces:
        pts = np.array([[p.x * w, p.y * h] for p in lm], dtype=np.float32)
        x0, y0 = pts.min(axis=0)
        x1, y1 = pts.max(axis=0)
        area = float((x1 - x0) * (y1 - y0))
        if area > best_area:
            best_area, best_pts = area, pts

    pts = best_pts
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)

    warnings: list[str] = []
    if len(faces) > 1:
        warnings.append(f"{len(faces)} faces theriyudhu. Perusa irukkura face mattum use aagum.")

    # Face frame-ku veliya cut aagudha
    if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
        warnings.append("Face photo-oda edge-la cut aagudhu. Muzhu face theriyara photo better.")

    # Bbox-a image kulla clip pannrom
    bx0, by0 = max(0, int(x0)), max(0, int(y0))
    bx1, by1 = min(w, int(x1)), min(h, int(y1))
    bw, bh = max(1, bx1 - bx0), max(1, by1 - by0)
    area_ratio = (bw * bh) / float(w * h)

    if area_ratio < MIN_FACE_AREA_RATIO:
        warnings.append("Face romba chinna-a irukku. Face-a close-up-a edutha photo use pannunga.")

    # Sharpness (blur check) + brightness: face crop-la mattum
    crop = cv2.cvtColor(bgr[by0:by1, bx0:bx1], cv2.COLOR_BGR2GRAY)
    crop = cv2.resize(crop, (256, 256), interpolation=cv2.INTER_AREA)
    sharpness = float(cv2.Laplacian(crop, cv2.CV_64F).var())
    brightness = float(crop.mean())

    if sharpness < 50:
        warnings.append("Photo blur-a irukku. Clear photo-la thaan face details nalla varum.")
    if brightness < 60:
        warnings.append("Photo romba dark-a irukku.")
    elif brightness > 200:
        warnings.append("Photo romba bright-a irukku.")

    oval = pts[FACE_OVAL].astype(np.int32)

    return FaceResult(
        face_count=len(faces),
        img_w=w,
        img_h=h,
        landmarks=pts,
        oval=oval,
        bbox=(bx0, by0, bw, bh),
        sharpness=round(sharpness, 1),
        brightness=round(brightness, 1),
        area_ratio=round(area_ratio, 4),
        warnings=warnings,
    )


def make_face_mask(result: FaceResult) -> np.ndarray:
    """Face oval-a vachu mask (face = 255, mathadhu = 0). Step 7-la use aagum."""
    mask = np.zeros((result.img_h, result.img_w), dtype=np.uint8)
    cv2.fillPoly(mask, [result.oval], 255)
    return mask


def draw_preview(bgr: np.ndarray, result: FaceResult) -> np.ndarray:
    """Face box + oval-a image mela varainju test-kaga kaattum."""
    out = bgr.copy()
    x, y, bw, bh = result.bbox
    thick = max(2, result.img_w // 400)
    cv2.rectangle(out, (x, y), (x + bw, y + bh), (0, 200, 0), thick)
    cv2.polylines(out, [result.oval], True, (0, 140, 255), thick)
    return out
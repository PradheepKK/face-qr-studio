# Project settings: file size limits, allowed types, paths, CORS, face model.
# Mattha files-um indha values-a inga irundhu dhaan edukkum.

from pathlib import Path

# backend/ folder-oda path
BASE_DIR = Path(__file__).resolve().parent.parent

# Temporary files inga mattum (processing mudinja udane delete aagum)
TMP_DIR = BASE_DIR / "tmp"

# ML model files inga irukkum
MODELS_DIR = BASE_DIR / "models"
FACE_LANDMARKER_PATH = MODELS_DIR / "face_landmarker.task"
FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

# App info
APP_NAME = "Face QR Studio API"
APP_VERSION = "0.1.0"

# File limits (frontend-la irukkura same values)
MAX_PERSON_MB = 10
MAX_QR_MB = 5

ALLOWED_PERSON_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_QR_TYPES = {"image/jpeg", "image/png"}

# Face detection-kku romba periya image-a indha size-ku kuraikkrom (speed-kaga)
MAX_IMAGE_SIDE = 2048

# Face image-la evvalavu perusa irukkanum (QR-la face theriya)
MIN_FACE_AREA_RATIO = 0.10

# Frontend-a mattum backend-a call panna allow pannrom (CORS).
CORS_ORIGIN_REGEX = (
    r"http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?"
    r"|https://.*\.vercel\.app"
)

# Person segmentation model (hair, neck, shoulders mask)
SEG_MODEL_PATH = MODELS_DIR / "selfie_segmenter.tflite"
SEG_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
    "selfie_segmenter/float16/latest/selfie_segmenter.tflite"
)

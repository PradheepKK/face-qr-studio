# Project settings: file size limits, allowed types, paths, CORS.
# Mattha files-um indha values-a inga irundhu dhaan edukkum.

from pathlib import Path

# backend/ folder-oda path
BASE_DIR = Path(__file__).resolve().parent.parent

# Temporary files inga mattum (processing mudinja udane delete aagum)
TMP_DIR = BASE_DIR / "tmp"

# App info
APP_NAME = "Face QR Studio API"
APP_VERSION = "0.1.0"

# File limits (frontend-la irukkura same values)
MAX_PERSON_MB = 10
MAX_QR_MB = 5

ALLOWED_PERSON_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_QR_TYPES = {"image/jpeg", "image/png"}

# Frontend-a mattum backend-a call panna allow pannrom (CORS).
# localhost + local network (192.168.x.x) allow, mobile-la test panna useful.
CORS_ORIGIN_REGEX = r"http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?"
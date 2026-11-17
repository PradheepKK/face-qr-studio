# GET /health : server run aagudha + ellaa libraries-um load aagudha nu check pannum.

import importlib
import platform

from fastapi import APIRouter

from app.config import APP_NAME, APP_VERSION

router = APIRouter()

# (display name, import name)
LIBRARIES = [
    ("opencv", "cv2"),
    ("numpy", "numpy"),
    ("pillow", "PIL"),
    ("mediapipe", "mediapipe"),
    ("qrcode", "qrcode"),
    ("zxingcpp", "zxingcpp"),
    ("fastapi", "fastapi"),
]


def check_library(import_name: str) -> dict:
    """Oru library import aagudha nu paarkkum. Fail aana error message-um kudukkum."""
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return {"ok": True, "version": str(version)}
    except Exception as e:  # DLL block, missing package ellaam inga pidikkum
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


@router.get("/health")
def health():
    libs = {name: check_library(mod) for name, mod in LIBRARIES}
    all_ok = all(item["ok"] for item in libs.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "app": APP_NAME,
        "version": APP_VERSION,
        "python": platform.python_version(),
        "libraries": libs,
    }
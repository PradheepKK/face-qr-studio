# Face model download script. Oru thadavai run pannina podhum.
# Run: python scripts\download_models.py   (backend folder-la irundhu)

import sys
import urllib.request
from pathlib import Path

# backend folder-a import path-la serkkrom (app.config edukka)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import FACE_LANDMARKER_PATH, FACE_LANDMARKER_URL, MODELS_DIR


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if FACE_LANDMARKER_PATH.exists() and FACE_LANDMARKER_PATH.stat().st_size > 1_000_000:
        print(f"Model already irukku: {FACE_LANDMARKER_PATH}")
        return

    print(f"Download aagudhu: {FACE_LANDMARKER_URL}")
    try:
        urllib.request.urlretrieve(FACE_LANDMARKER_URL, FACE_LANDMARKER_PATH)
    except Exception as e:
        print(f"Download fail: {e}")
        print("Manual-a download panna: browser-la indha URL open pannunga:")
        print(FACE_LANDMARKER_URL)
        print(f"Download aana file-a inga vainga: {FACE_LANDMARKER_PATH}")
        sys.exit(1)

    size_mb = FACE_LANDMARKER_PATH.stat().st_size / (1024 * 1024)
    print(f"Done. Saved: {FACE_LANDMARKER_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
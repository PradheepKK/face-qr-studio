# Models download script. Run: python scripts\download_models.py

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import (
    FACE_LANDMARKER_PATH,
    FACE_LANDMARKER_URL,
    MODELS_DIR,
    SEG_MODEL_PATH,
    SEG_MODEL_URL,
)


def fetch(url: str, path: Path) -> bool:
    if path.exists() and path.stat().st_size > 100_000:
        print(f"Already irukku: {path.name}")
        return True
    print(f"Download aagudhu: {url}")
    try:
        urllib.request.urlretrieve(url, path)
    except Exception as e:
        print(f"Download fail: {e}\nManual: browser-la {url} open pannitu {path} la vainga")
        return False
    print(f"Saved: {path.name} ({path.stat().st_size / 1024 / 1024:.1f} MB)")
    return True


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ok1 = fetch(FACE_LANDMARKER_URL, FACE_LANDMARKER_PATH)
    ok2 = fetch(SEG_MODEL_URL, SEG_MODEL_PATH)
    sys.exit(0 if (ok1 and ok2) else 1)


if __name__ == "__main__":
    main()
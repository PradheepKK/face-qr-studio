# Image bytes <-> numpy conversion. EXIF rotation-um handle pannum
# (mobile photos sila time sideways-a irukkum).

import io

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

# Decompression bomb (periya fake image) attack-a thadukka
Image.MAX_IMAGE_PIXELS = 50_000_000


def decode_image_bgr(data: bytes, max_side: int | None = None) -> tuple[np.ndarray, bool]:
    """Bytes-a OpenCV BGR array-a maathum. Periya image-na max_side-ku kuraikkum.
    Return: (image, downscaled_aa)"""
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)  # phone rotation sari pannum
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise ValueError(f"Image-a padikka mudiyala: {e}") from e

    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    downscaled = False
    if max_side:
        h, w = bgr.shape[:2]
        longest = max(h, w)
        if longest > max_side:
            scale = max_side / longest
            bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            downscaled = True

    return bgr, downscaled


def encode_png(bgr: np.ndarray) -> bytes:
    """BGR array-a PNG bytes-a maathum."""
    ok, buf = cv2.imencode(".png", bgr)
    if not ok:
        raise ValueError("PNG encode fail aachu")
    return buf.tobytes()
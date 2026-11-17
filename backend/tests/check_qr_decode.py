# Real round-trip test: QR generate -> kedukki -> decode -> exact payload compare.
# Run (backend folder-la, venv activate-la):  python tests\check_qr_decode.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import qrcode

from app.core.qr_decode import NoQrError, decode_qr


def make_qr(data: str, box: int = 10, border: int = 4) -> np.ndarray:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def rotate(img: np.ndarray, angle: float) -> np.ndarray:
    pad = max(img.shape[:2]) // 3
    img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, m, (w, h), borderValue=(255, 255, 255))


def jpeg(img: np.ndarray, quality: int) -> np.ndarray:
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def low_contrast(img: np.ndarray) -> np.ndarray:
    return (img.astype(np.float32) * 0.45 + 120).astype(np.uint8)


PAYLOADS = {
    "upi": "upi://pay?pa=test.user@okhdfcbank&pn=Test%20User&am=150.00&cu=INR&tn=Test",
    "url": "https://example.com/pay?id=12345&ref=abc",
    "tamil": "வணக்கம் Face QR Studio 12345",
}

# Kattayam pass aaganum
REQUIRED = {
    "plain": lambda im: im,
    "small (box=3)": None,  # thaniya generate pannrom
    "rotate 90": lambda im: cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE),
    "rotate 180": lambda im: cv2.rotate(im, cv2.ROTATE_180),
    "jpeg q40": lambda im: jpeg(im, 40),
    "blur": lambda im: cv2.GaussianBlur(im, (5, 5), 0),
}

# Kashtamaana cases (pass aana nalladhu, fail aana test fail illa)
STRESS = {
    "rotate 20 deg": lambda im: rotate(im, 20),
    "low contrast": low_contrast,
    "no quiet zone": None,  # border=0
}


def run_case(name: str, data: str, img: np.ndarray) -> bool:
    try:
        r = decode_qr(img)
        ok = r.payload_bytes == data.encode("utf-8")
        mark = "PASS" if ok else "WRONG PAYLOAD"
        print(f"   [{mark}] {name} (zxing={r.zxing_ok}, opencv={r.opencv_ok}, agree={r.decoders_agree})")
        return ok
    except NoQrError:
        print(f"   [FAIL] {name} (decode aagala)")
        return False


def main() -> None:
    required_fail = 0
    for label, data in PAYLOADS.items():
        print(f"\nPayload: {label}")
        base = make_qr(data)
        for name, fn in REQUIRED.items():
            img = make_qr(data, box=3) if name.startswith("small") else fn(base)
            if not run_case(name, data, img):
                required_fail += 1
        for name, fn in STRESS.items():
            img = make_qr(data, border=0) if name == "no quiet zone" else fn(base)
            run_case(name + " (stress)", data, img)

    # Negative test: QR illaadha random noise-la false decode aaga koodadhu
    print("\nNegative test (QR illa)")
    noise = np.random.default_rng(0).integers(0, 255, (400, 400, 3), dtype=np.uint8)
    try:
        decode_qr(noise)
        print("   [FAIL] noise-la QR decode aachu (idhu thappu)")
        required_fail += 1
    except NoQrError:
        print("   [PASS] noise-la QR illa nu sariya sonnadhu")

    print("\n" + ("ALL REQUIRED TESTS PASSED" if required_fail == 0 else f"{required_fail} REQUIRED TEST(S) FAILED"))
    sys.exit(1 if required_fail else 0)


if __name__ == "__main__":
    main()
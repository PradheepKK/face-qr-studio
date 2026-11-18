# Face QR render + real decode check.
# Run (backend folder, venv activate-la):
#   python tests\check_face_qr.py "C:\path\to\photo.jpg"
#   python tests\check_face_qr.py "C:\path\to\photo.jpg" "C:\path\to\payment_qr.png"

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import qrcode

from app.core.face_detect import detect_face
from app.core.face_mapper import build_plan
from app.core.qr_decode import NoQrError, decode_qr
from app.core.renderer import render
from app.utils.image_io import decode_image_bgr

SAMPLE_PAYLOAD = "upi://pay?pa=test.user@okhdfcbank&pn=Test%20User&am=150.00&cu=INR&tn=Test"


def sample_qr_image() -> np.ndarray:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(SAMPLE_PAYLOAD)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def try_decode(img: np.ndarray, expected: bytes) -> bool:
    try:
        return decode_qr(img).payload_bytes == expected
    except NoQrError:
        return False


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python tests\\check_face_qr.py "photo.jpg" ["payment_qr.png"]')
        sys.exit(2)

    photo, qr_path = Path(sys.argv[1]), (Path(sys.argv[2]) if len(sys.argv) > 2 else None)

    person, _ = decode_image_bgr(photo.read_bytes(), max_side=2048)
    face = detect_face(person)
    if qr_path:
        qr_img, _ = decode_image_bgr(qr_path.read_bytes(), max_side=2048)
    else:
        qr_img = sample_qr_image()
    qr = decode_qr(qr_img)

    print(f"Face: {face.face_count} face, warnings={face.warnings}")
    print(f"QR: type={qr.payload_type}, best_ec={qr.best_ec_level}, min_version={qr.qr_version}")

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)

    full_fail = 0
    for style in ("face", "portrait", "minimal"):
        for res in (1024, 2048):
            t0 = time.time()
            plan = build_plan(person, face, qr.payload_bytes, qr.best_ec_level, qr.qr_version, style=style)
            img = render(plan, "#000000", "#ffffff", res)
            secs = time.time() - t0

            path = out_dir / f"{style}_{res}.png"
            cv2.imwrite(str(path), img)

            results = []
            for scale in (1.0, 0.5):
                im = img if scale == 1.0 else cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                ok = try_decode(im, qr.payload_bytes)
                results.append(f"{int(scale * 100)}%={'OK' if ok else 'FAIL'}")
                if scale == 1.0 and not ok:
                    full_fail += 1

            print(
                f"[{style:8s} {res}px] v{plan.version} mask={plan.matrix.mask} "
                f"center={plan.center_frac:.2f} seg={plan.segmentation} "
                f"{secs:.1f}s -> {' '.join(results)}"
            )

    print(f"\nOutput images: {out_dir}")
    print("100% decode fail count:", full_fail)
    sys.exit(1 if full_fail else 0)


if __name__ == "__main__":
    main()
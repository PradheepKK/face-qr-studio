# Halftone test: render + real decode + reference compare.
# Run (backend folder, venv activate-la):
#   python tests\check_halftone.py "C:\path\photo.jpg" ["C:\path\payment_qr.png"]

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import qrcode

from app.core.face_detect import detect_face
from app.core.halftone_loop import run_halftone_loop
from app.core.qr_decode import decode_qr
from app.utils.image_io import decode_image_bgr

SAMPLE = "upi://pay?pa=test.user@okhdfcbank&pn=Test%20User&am=150.00&cu=INR&tn=Test"


def sample_qr_image() -> np.ndarray:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(SAMPLE)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python tests\\check_halftone.py "photo.jpg" ["payment_qr.png"]')
        sys.exit(2)

    person, _ = decode_image_bgr(Path(sys.argv[1]).read_bytes(), max_side=2048)
    face = detect_face(person)
    if len(sys.argv) > 2:
        qr_img, _ = decode_image_bgr(Path(sys.argv[2]).read_bytes(), max_side=2048)
    else:
        qr_img = sample_qr_image()
    qr = decode_qr(qr_img)
    print(f"QR: type={qr.payload_type}, best_ec={qr.best_ec_level}, min_version={qr.qr_version}")

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    ref_path = Path(__file__).resolve().parent / "reference" / "style1.jpg"

    failures = 0
    for res in (1024, 2048):
        t0 = time.time()
        r = run_halftone_loop(person, face, qr.payload_bytes, qr.best_ec_level, qr.qr_version, res)
        secs = time.time() - t0

        cv2.imwrite(str(out_dir / f"halftone_{res}.png"), r.image)
        print(f"\n[{res}px] verified={r.verified} attempts={len(r.attempts)} "
              f"v{r.plan.version} center={r.plan.center_frac:.2f} blend={r.plan.blend:.2f} "
              f"mask={r.plan.matrix.mask} seg={r.plan.segmentation} {secs:.1f}s")
        print("   ", r.report.summary())
        print("   ", r.report.detail())
        for a in r.attempts:
            print(f"    attempt {a.number}: v{a.version} c={a.center:.2f} -> "
                  f"{a.error or f'{a.passed}/{a.total}'} {'(verified)' if a.verified else ''}")

        if r.verified:
            try:
                same = decode_qr(r.image).payload_bytes == qr.payload_bytes
            except Exception:
                same = False
            print(f"    independent decode exact match: {same}")
            if not same:
                failures += 1

        # Dhoorathula paartha maari (face theriyudha nu check panna)
        if res == 2048:
            far = cv2.resize(r.image, (256, 256), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(out_dir / "halftone_far_256.png"), far)

            if ref_path.exists():
                ref = cv2.imread(str(ref_path))
                if ref is not None:
                    a = cv2.resize(ref, (800, 800), interpolation=cv2.INTER_AREA)
                    b = cv2.resize(r.image, (800, 800), interpolation=cv2.INTER_AREA)
                    cv2.imwrite(str(out_dir / "halftone_vs_reference.png"), np.hstack([a, b]))
                    print("    compare image: halftone_vs_reference.png (left=reference, right=ours)")

    print(f"\nOutput folder: {out_dir}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
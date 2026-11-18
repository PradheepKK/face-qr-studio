# Step 8 test: validation + retry loop real-a work aagudha.
# Run (backend folder, venv activate-la):
#   python tests\check_step8.py "C:\path\photo.jpg" ["C:\path\payment_qr.png"]

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
import qrcode

from app.core.face_detect import detect_face
from app.core.face_mapper import build_plan
from app.core.qr_decode import _capacity, decode_qr
from app.core.renderer import render
from app.core.retry_loop import run_retry_loop
from app.core.validator import validate
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
        print('Usage: python tests\\check_step8.py "photo.jpg" ["payment_qr.png"]')
        sys.exit(2)

    person, _ = decode_image_bgr(Path(sys.argv[1]).read_bytes(), max_side=2048)
    face = detect_face(person)
    if len(sys.argv) > 2:
        qr_img, _ = decode_image_bgr(Path(sys.argv[2]).read_bytes(), max_side=2048)
    else:
        qr_img = sample_qr_image()
    qr = decode_qr(qr_img)

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    failures = 0

    # ---------- Test A: full pipeline ----------
    print("\n[A] Full pipeline (retry loop)")
    for style in ("face", "portrait", "minimal"):
        t0 = time.time()
        res = run_retry_loop(
            person, face, qr.payload_bytes, qr.best_ec_level, qr.qr_version,
            style=style, face_visibility=70, density=50, contrast=50,
            qr_color="#000000", bg_color="#ffffff", resolution=2048,
        )
        secs = time.time() - t0
        cv2.imwrite(str(out_dir / f"step8_{style}.png"), res.image)
        print(f"  {style:8s}: verified={res.verified} attempts={len(res.attempts)} "
              f"final=v{res.plan.version}/center={res.plan.center_frac:.2f} {secs:.1f}s")
        print(f"            {res.report.summary()}")
        print(f"            {res.report.detail()}")
        # Independent re-check: Step 6-oda decoder-um same payload-a thara venum
        if res.verified:
            try:
                same = decode_qr(res.image).payload_bytes == qr.payload_bytes
            except Exception:
                same = False
            print(f"            independent decode_qr exact match: {same}")
            if not same:
                failures += 1

    # ---------- Test B: thappu payload ----------
    print("\n[B] Thappu payload image (Verified aaga koodadhu)")
    wrong = (SAMPLE + "X").encode("utf-8")
    ec, ver, _ = _capacity(wrong, wrong.decode("utf-8"))
    plan = build_plan(person, face, wrong, ec, ver, style="face")
    img = render(plan, "#000000", "#ffffff", 2048)
    rep = validate(img, qr.payload_bytes)  # vera payload-oda compare
    ok = not rep.verified
    print(f"  verified={rep.verified} -> {'PASS' if ok else 'FAIL'}")
    failures += 0 if ok else 1

    # ---------- Test C: noise ----------
    print("\n[C] Noise image (Verified aaga koodadhu)")
    noise = np.random.default_rng(1).integers(0, 255, (1024, 1024, 3), dtype=np.uint8)
    rep = validate(noise, qr.payload_bytes)
    ok = not rep.verified
    print(f"  verified={rep.verified} -> {'PASS' if ok else 'FAIL'}")
    failures += 0 if ok else 1

    print(f"\nOutput: {out_dir}")
    print("ALL SAFETY TESTS PASSED" if failures == 0 else f"{failures} SAFETY TEST(S) FAILED")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
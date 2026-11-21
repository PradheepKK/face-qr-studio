# Endha (version, center, alignment) combination-la endha checks fail aagudhu nu kaattum.
# Run: python tests\diag_halftone.py "photo.jpg" "payment_qr.png"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.face_detect import detect_face
from app.core.halftone import prepare, render_halftone
from app.core.qr_decode import decode_qr
from app.core.validator import validate
from app.utils.image_io import decode_image_bgr

person, _ = decode_image_bgr(Path(sys.argv[1]).read_bytes(), max_side=2048)
face = detect_face(person)
qr_img, _ = decode_image_bgr(Path(sys.argv[2]).read_bytes(), max_side=2048)
qr = decode_qr(qr_img)
prep = prepare(person, face)

for ver in (12, 10, 8):
    for cen, blend in ((0.30, 0.0), (0.42, 0.12), (0.55, 0.30)):
        for afree in (True, False):
            img, plan = render_halftone(
                prep, qr.payload_bytes, qr.best_ec_level, ver, cen, blend, 2048, {}, afree
            )
            rep = validate(img, qr.payload_bytes)
            failed = [c.label for c in rep.checks if not c.ok]
            print(f"v{ver} c={cen:.2f} b={blend:.2f} align_free={afree!s:5} "
                  f"pass={rep.passed}/{rep.total} FAILED: {failed}")
# Upload panna file-a validate pannum: content-type, size, unmaiyaana file signature.
# Extension-a mattum nambaama, file-oda first bytes-a paarkkrom.

from fastapi import HTTPException, UploadFile

CHUNK_SIZE = 1024 * 1024  # 1 MB


def _sniff_type(head: bytes) -> str | None:
    """File-oda first bytes-la irundhu unmaiyaana image type kandupidikkum."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


async def read_validated_image(
    file: UploadFile, allowed_types: set[str], max_mb: int
) -> bytes:
    """Validate pannitu file bytes-a memory-la return pannum. Disk-la save aagaadhu."""
    if file.content_type not in allowed_types:
        names = ", ".join(sorted(t.split("/")[1].upper() for t in allowed_types))
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed: {names}")

    max_bytes = max_mb * 1024 * 1024
    buffer = bytearray()
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        # Periya file-na ulla padikkaama udane niruthirom
        if len(buffer) > max_bytes:
            raise HTTPException(status_code=413, detail=f"File is too large. Max size {max_mb} MB.")

    if len(buffer) == 0:
        raise HTTPException(status_code=400, detail="The file is empty.")

    real_type = _sniff_type(bytes(buffer[:16]))
    if real_type is None or real_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail="This is not a valid image file.",
        )

    return bytes(buffer)
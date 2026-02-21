from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1 MB

MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",  # also check for WEBP at offset 8
}


async def validate_image(file: UploadFile) -> bytes:
    """Read, validate magic bytes + MIME, enforce size limit."""
    content = await file.read()

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Image too large (max 1MB)")

    detected_type = None
    for magic, mime in MAGIC_BYTES.items():
        if content[: len(magic)] == magic:
            if mime == "image/webp":
                # Additional check for WEBP signature at offset 8
                if len(content) >= 12 and content[8:12] == b"WEBP":
                    detected_type = mime
            else:
                detected_type = mime
            break

    if detected_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Invalid image type. Allowed: JPEG, PNG, WebP")

    return content

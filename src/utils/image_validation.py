import uuid

from fastapi import HTTPException, UploadFile

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1 MB

MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",  # also check for WEBP at offset 8
}

MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def sanitize_filename(original: str | None, detected_type: str) -> str:
    """Generate a safe UUID-based filename with correct extension."""
    ext = MIME_TO_EXT.get(detected_type, ".bin")
    return f"{uuid.uuid4().hex}{ext}"


async def validate_image(file: UploadFile) -> tuple[bytes, str]:
    """Read, validate magic bytes + MIME, enforce size limit.

    Returns (content, safe_filename).
    """
    content = await file.read()

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Image too large (max 1MB)")

    detected_type = None
    for magic, mime in MAGIC_BYTES.items():
        if content[: len(magic)] == magic:
            if mime == "image/webp":
                if len(content) >= 12 and content[8:12] == b"WEBP":
                    detected_type = mime
            else:
                detected_type = mime
            break

    if detected_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Invalid image type. Allowed: JPEG, PNG, WebP")

    safe_name = sanitize_filename(file.filename, detected_type)
    return content, safe_name

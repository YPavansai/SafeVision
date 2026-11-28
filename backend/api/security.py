import logging
import os
import re
import uuid
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import cv2
import numpy as np
from django.core.files.base import ContentFile

logger = logging.getLogger('safevision.security')

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_BASE64_BYTES = 10 * 1024 * 1024
_SAFE_NAME_RE = re.compile(r'[^A-Za-z0-9._-]+')


def sanitize_display_filename(filename, fallback='upload.jpg'):
    """Strips directory components and unsafe characters from user-supplied filenames."""
    base = os.path.basename(str(filename or '')).strip()
    cleaned = _SAFE_NAME_RE.sub('_', base).strip('._')
    return (cleaned or fallback)[:180]


def validate_safe_path_in_dir(base_dir, user_filename, allowed_extensions=None):
    """
    Prevents directory traversal by ensuring the resolved target path stays inside base_dir.
    Raises ValueError on invalid names or traversal attempts.
    """
    if not user_filename or not isinstance(user_filename, str):
        raise ValueError("Filename is required.")
    if '\x00' in user_filename or '/' in user_filename or '\\' in user_filename or '..' in user_filename:
        logger.warning("Blocked potential path traversal attempt: %r", user_filename[:80])
        raise ValueError("Invalid filename.")

    ext = os.path.splitext(user_filename)[1].lower()
    if allowed_extensions and ext not in allowed_extensions:
        raise ValueError(f"Unsupported file format '{ext}'.")

    root = Path(base_dir).resolve()
    target = (root / user_filename).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        logger.warning("Blocked path escape outside %s: %r", root, user_filename[:80])
        raise ValueError("Invalid file path.")
    return str(target)


def validate_and_prepare_image(uploaded_file, max_bytes=MAX_IMAGE_BYTES):
    """
    Validates uploaded image extension, size, Pillow structural integrity, and OpenCV decoding.
    Returns (safe_content_file, sanitized_original_name, decoded_bgr_np).
    Raises ValueError on validation failure.
    """
    if uploaded_file is None:
        raise ValueError("No image file provided.")

    orig_name = sanitize_display_filename(getattr(uploaded_file, 'name', 'image.jpg'))
    ext = os.path.splitext(orig_name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format '{ext}'. Allowed formats: JPG, JPEG, PNG, WEBP, BMP."
        )

    size = getattr(uploaded_file, 'size', None)
    if size is not None and size > max_bytes:
        raise ValueError("Image file exceeds the 15MB size limit.")

    file_bytes = uploaded_file.read(max_bytes + 1)
    if not file_bytes:
        raise ValueError("Uploaded image file is empty.")
    if len(file_bytes) > max_bytes:
        raise ValueError("Image file exceeds the 15MB size limit.")

    # Verify image structure via Pillow (catches spoofed extensions & truncated headers)
    import io
    try:
        with Image.open(io.BytesIO(file_bytes)) as pil_img:
            pil_img.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise ValueError("Uploaded file is corrupted or not a valid image.") from exc

    # Decode via OpenCV to guarantee CV pipeline compatibility
    nparr = np.frombuffer(file_bytes, np.uint8)
    decoded = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if decoded is None or decoded.size == 0:
        raise ValueError("Uploaded file is corrupted or could not be decoded as an image.")

    safe_storage_name = f"{uuid.uuid4().hex}{ext}"
    return ContentFile(file_bytes, name=safe_storage_name), orig_name, decoded


def decode_base64_image(data_uri, max_bytes=MAX_BASE64_BYTES):
    """Safely decodes a base64 image payload with strict size & decode checks."""
    import base64

    if not data_uri or not isinstance(data_uri, str):
        raise ValueError("Image payload is required.")
    encoded_data = data_uri.split(',', 1)[1] if ',' in data_uri else data_uri
    if len(encoded_data) > int(max_bytes * 1.4):
        raise ValueError("Camera frame payload exceeds maximum allowed size.")
    try:
        raw_bytes = base64.b64decode(encoded_data, validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 image encoding.") from exc
    if len(raw_bytes) > max_bytes:
        raise ValueError("Decoded image exceeds maximum allowed size.")

    nparr = np.frombuffer(raw_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None or img.size == 0:
        raise ValueError("Invalid or corrupted image frame data.")
    return img

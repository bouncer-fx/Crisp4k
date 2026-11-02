import io
import uuid
import httpx
from PIL import Image
from . import config

async def get_user(url, key, token):
    """Ask Supabase who owns this login token. Returns user dict or None."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url + "/auth/v1/user",
                        headers={"apikey": key, "Authorization": "Bearer " + token})
    if r.status_code != 200:
        return None
    return r.json()

def validate_image(data, content_type, max_mb):
    if content_type not in config.ALLOWED_TYPES:
        return "Only JPG, PNG or WEBP images are allowed."
    if len(data) > max_mb * 1024 * 1024:
        return "File is too large. Maximum is %d MB." % max_mb
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        w, h = img.size
    except Exception:
        return "That file is not a valid image."
    if min(w, h) < config.MIN_SIDE:
        return "Image is too small."
    if max(w, h) > config.MAX_SIDE:
        return "Image dimensions are too large."
    return None

async def store_and_record(url, key, user_id, data, content_type, mode):
    ext = config.ALLOWED_TYPES[content_type]
    path = "%s/%s.%s" % (user_id, uuid.uuid4(), ext)
    h = {"apikey": key, "Authorization": "Bearer " + key}
    async with httpx.AsyncClient(timeout=60) as c:
        up = await c.post(url + "/storage/v1/object/" + config.BUCKET + "/" + path,
                          headers={**h, "Content-Type": content_type}, content=data)
        if up.status_code not in (200, 201):
            print("STORAGE ERROR", up.status_code, up.text[:300], flush=True)
            return None, "Storage upload failed."
        row = await c.post(url + "/rest/v1/enhancements",
                           headers={**h, "Content-Type": "application/json",
                                    "Prefer": "return=representation"},
                           json={"user_id": user_id, "original_path": path,
                                 "enhancement_mode": mode, "status": "PENDING"})
        if row.status_code not in (200, 201):
            return None, "Could not record the upload."
    return row.json()[0], None

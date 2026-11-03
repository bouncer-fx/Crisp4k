import io, os, sys, time, asyncio
import httpx
from PIL import Image, ImageOps
from . import config

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "enhancement-engine"))
from processors.classical import ClassicalProcessor, plan

def _preview(data, mode, params=None):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    img.thumbnail((1350, 1080), Image.LANCZOS)
    out = ClassicalProcessor().process(img, mode, target=1350, params=params)
    out.thumbnail((1350, 1080), Image.LANCZOS)
    b = io.BytesIO()
    out.save(b, "JPEG", quality=88)
    return b.getvalue()

def _full(data, mode, params=None):
    out = ClassicalProcessor().process(Image.open(io.BytesIO(data)), mode, params=params)
    b = io.BytesIO()
    out.save(b, "JPEG", quality=95, subsampling=0, optimize=True)
    return b.getvalue()

def plan_for(data, mode):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    return plan(img, mode)

async def sign(url, key, path):
    h = {"apikey": key, "Authorization": "Bearer " + key}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url + "/storage/v1/object/sign/" + config.BUCKET + "/" + path,
                         headers=h, json={"expiresIn": 3600})
    if r.status_code != 200:
        return None
    return url + "/storage/v1" + r.json()["signedURL"]

async def run_job(url, key, job_id, original_path, mode, user_id=None, cost=0, data=None):
    h = {"apikey": key, "Authorization": "Bearer " + key}
    t = time.time()
    base = original_path.rsplit(".", 1)[0]
    enh = base + "_enhanced.jpg"
    prev = base + "_preview.jpg"

    async def setstatus(patch):
        async with httpx.AsyncClient(timeout=30) as c:
            await c.patch(url + "/rest/v1/enhancements?id=eq." + job_id,
                          headers={**h, "Content-Type": "application/json"}, json=patch)

    async def put(c, path, content):
        r = await c.post(url + "/storage/v1/object/" + config.BUCKET + "/" + path,
                         headers={**h, "Content-Type": "image/jpeg", "x-upsert": "true"}, content=content)
        r.raise_for_status()

    try:
        async with httpx.AsyncClient(timeout=120) as c:
            if data is None:
                r = await c.get(url + "/storage/v1/object/" + config.BUCKET + "/" + original_path, headers=h)
                r.raise_for_status()
                data = r.content
            params, _ = await asyncio.to_thread(plan_for, data, mode)
            pv = await asyncio.to_thread(_preview, data, mode, params)
            await put(c, prev, pv)
            await setstatus({"status": "PROCESSING", "enhanced_path": enh})
            out = await asyncio.to_thread(_full, data, mode, params)
            await put(c, enh, out)
        await setstatus({"status": "COMPLETED", "enhanced_path": enh,
                         "processing_time": round(time.time() - t, 2)})
    except Exception:
        await setstatus({"status": "FAILED"})
        if user_id and cost:
            from .credits import adjust
            await adjust(url, key, user_id, cost)

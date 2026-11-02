import io, os, sys, time, asyncio
import httpx
from PIL import Image
from . import config

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "enhancement-engine"))
from processors.classical import ClassicalProcessor

def _run(data, mode):
    img = Image.open(io.BytesIO(data))
    out = ClassicalProcessor().process(img, mode)
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=95)
    return buf.getvalue()

async def sign(url, key, path):
    h = {"apikey": key, "Authorization": "Bearer " + key}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(url + "/storage/v1/object/sign/" + config.BUCKET + "/" + path,
                         headers=h, json={"expiresIn": 3600})
    if r.status_code != 200:
        return None
    return url + "/storage/v1" + r.json()["signedURL"]

async def run_job(url, key, job_id, original_path, mode):
    h = {"apikey": key, "Authorization": "Bearer " + key}
    t = time.time()

    async def setstatus(patch):
        async with httpx.AsyncClient(timeout=30) as c:
            await c.patch(url + "/rest/v1/enhancements?id=eq." + job_id,
                          headers={**h, "Content-Type": "application/json"}, json=patch)
    try:
        await setstatus({"status": "PROCESSING"})
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.get(url + "/storage/v1/object/" + config.BUCKET + "/" + original_path, headers=h)
            r.raise_for_status()
            out = await asyncio.to_thread(_run, r.content, mode)
            enh = original_path.rsplit(".", 1)[0] + "_enhanced.jpg"
            up = await c.post(url + "/storage/v1/object/" + config.BUCKET + "/" + enh,
                              headers={**h, "Content-Type": "image/jpeg"}, content=out)
            up.raise_for_status()
        await setstatus({"status": "COMPLETED", "enhanced_path": enh,
                         "processing_time": round(time.time() - t, 2)})
    except Exception:
        await setstatus({"status": "FAILED"})

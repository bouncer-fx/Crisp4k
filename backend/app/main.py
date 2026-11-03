import os
import asyncio
import uuid
import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.background import BackgroundTask
from .process import run_job, sign, plan_for
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

def load_env():
    path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://127.0.0.1:8080,http://localhost:8080").split(",") if o.strip()]

async def health(request):
    return JSONResponse({"status": "ok", "service": "crisp4k-backend"})

async def db_check(request):
    if not URL or not KEY:
        return JSONResponse({"ok": False, "error": "env not set"}, status_code=500)
    headers = {"apikey": KEY, "Authorization": "Bearer " + KEY}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(URL + "/rest/v1/credits?select=user_id&limit=1", headers=headers)
    return JSONResponse({"ok": r.status_code == 200, "supabase_status": r.status_code})


from .uploads import get_user, validate_image, store_and_record
from .credits import adjust, test_mode, rate_limited
from .extra import make_routes
from . import config

async def upload(request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": "Please log in first."}, status_code=401)
    user = await get_user(URL, KEY, auth[7:])
    if not user:
        return JSONResponse({"error": "Invalid or expired login."}, status_code=401)
    if rate_limited(user["id"]):
        return JSONResponse({"error": "Too many uploads. Please wait a minute."}, status_code=429)
    form = await request.form()
    f = form.get("file")
    mode = form.get("mode", "standard")
    if f is None or not hasattr(f, "read"):
        return JSONResponse({"error": "No file received."}, status_code=400)
    if mode not in ("standard", "pro", "4k"):
        return JSONResponse({"error": "Unknown enhancement mode."}, status_code=400)
    data = await f.read()
    err = validate_image(data, f.content_type, config.MAX_MB_FREE)
    if err:
        return JSONResponse({"error": err}, status_code=400)
    cost = config.CREDIT_COST[mode]
    charged = not test_mode()
    if charged:
        ok, cerr = await adjust(URL, KEY, user["id"], -cost)
        if not ok:
            return JSONResponse({"error": cerr}, status_code=402)
    row, err = await store_and_record(URL, KEY, user["id"], data, f.content_type, mode)
    if err:
        if charged:
            await adjust(URL, KEY, user["id"], cost)
        return JSONResponse({"error": err}, status_code=500)
    notes = await asyncio.to_thread(lambda: plan_for(data, mode)[1])
    return JSONResponse({"id": row["id"], "status": row["status"], "notes": notes},
        background=BackgroundTask(run_job, URL, KEY, row["id"], row["original_path"], mode,
            user["id"], cost if charged else 0, data))

async def job_status(request):
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": "Please log in first."}, status_code=401)
    user = await get_user(URL, KEY, auth[7:])
    if not user:
        return JSONResponse({"error": "Invalid or expired login."}, status_code=401)
    try:
        jid = str(uuid.UUID(request.path_params["job_id"]))
    except ValueError:
        return JSONResponse({"error": "Bad job id."}, status_code=400)
    h = {"apikey": KEY, "Authorization": "Bearer " + KEY}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(URL + "/rest/v1/enhancements?id=eq." + jid + "&user_id=eq." + user["id"] + "&select=*", headers=h)
    rows = r.json() if r.status_code == 200 else []
    if not rows:
        return JSONResponse({"error": "Not found."}, status_code=404)
    row = rows[0]
    out = {"id": row["id"], "status": row["status"]}
    if row.get("enhanced_path") and row["status"] in ("PROCESSING", "COMPLETED"):
        out["original_url"] = await sign(URL, KEY, row["original_path"])
        out["preview_url"] = await sign(URL, KEY, row["enhanced_path"].replace("_enhanced.jpg", "_preview.jpg"))
        if row["status"] == "COMPLETED":
            out["enhanced_url"] = await sign(URL, KEY, row["enhanced_path"])
    return JSONResponse(out)

app = Starlette(routes=make_routes(URL, KEY) + [
    Route("/api/health", health),
    Route("/api/dbcheck", db_check),
    Route("/api/upload", upload, methods=["POST"]),
    Route("/api/enhance/{job_id}", job_status),
], middleware=[Middleware(CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["POST", "GET", "DELETE"], allow_headers=["authorization", "content-type"])])

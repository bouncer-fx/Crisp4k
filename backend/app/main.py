import os
import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

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

async def health(request):
    return JSONResponse({"status": "ok", "service": "crisp4k-backend"})

async def db_check(request):
    if not URL or not KEY:
        return JSONResponse({"ok": False, "error": "env not set"}, status_code=500)
    headers = {"apikey": KEY, "Authorization": "Bearer " + KEY}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(URL + "/rest/v1/credits?select=user_id&limit=1", headers=headers)
    return JSONResponse({"ok": r.status_code == 200, "supabase_status": r.status_code})

app = Starlette(routes=[
    Route("/api/health", health),
    Route("/api/dbcheck", db_check),
])

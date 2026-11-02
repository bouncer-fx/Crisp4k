import uuid
import httpx
from starlette.responses import JSONResponse
from starlette.routing import Route
from .uploads import get_user
from .process import sign
from .credits import test_mode
from . import config

def make_routes(URL, KEY):
    H = {"apikey": KEY, "Authorization": "Bearer " + KEY}

    async def auth(request):
        a = request.headers.get("authorization", "")
        if not a.startswith("Bearer "):
            return None
        return await get_user(URL, KEY, a[7:])

    async def credits(request):
        user = await auth(request)
        if not user:
            return JSONResponse({"error": "Please log in first."}, status_code=401)
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(URL + "/rest/v1/credits?user_id=eq." + user["id"] + "&select=available_credits", headers=H)
        rows = r.json() if r.status_code == 200 else []
        return JSONResponse({"credits": rows[0]["available_credits"] if rows else 0, "test_mode": test_mode()})

    async def history(request):
        user = await auth(request)
        if not user:
            return JSONResponse({"error": "Please log in first."}, status_code=401)
        q = "/rest/v1/enhancements?user_id=eq." + user["id"] + "&select=id,enhancement_mode,status,created_at,processing_time,original_path,enhanced_path&order=created_at.desc&limit=10"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(URL + q, headers=H)
        rows = r.json() if r.status_code == 200 else []
        items = []
        for row in rows:
            item = {k: row[k] for k in ("id", "enhancement_mode", "status", "created_at", "processing_time")}
            if row["status"] == "COMPLETED" and row.get("enhanced_path"):
                item["enhanced_url"] = await sign(URL, KEY, row["enhanced_path"])
                item["preview_url"] = await sign(URL, KEY, row["enhanced_path"].replace("_enhanced.jpg", "_preview.jpg"))
                item["original_url"] = await sign(URL, KEY, row["original_path"])
            items.append(item)
        return JSONResponse({"items": items})

    async def delete_job(request):
        user = await auth(request)
        if not user:
            return JSONResponse({"error": "Please log in first."}, status_code=401)
        try:
            jid = str(uuid.UUID(request.path_params["job_id"]))
        except ValueError:
            return JSONResponse({"error": "Bad job id."}, status_code=400)
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(URL + "/rest/v1/enhancements?id=eq." + jid + "&user_id=eq." + user["id"] + "&select=original_path,enhanced_path", headers=H)
            rows = r.json() if r.status_code == 200 else []
            if not rows:
                return JSONResponse({"error": "Not found."}, status_code=404)
            paths = [p for p in (rows[0]["original_path"], rows[0].get("enhanced_path")) if p]
            if rows[0].get("enhanced_path"):
                paths.append(rows[0]["enhanced_path"].replace("_enhanced.jpg", "_preview.jpg"))
            await c.request("DELETE", URL + "/storage/v1/object/" + config.BUCKET,
                            headers={**H, "Content-Type": "application/json"}, json={"prefixes": paths})
            await c.delete(URL + "/rest/v1/enhancements?id=eq." + jid + "&user_id=eq." + user["id"], headers=H)
        return JSONResponse({"deleted": True})

    return [
        Route("/api/credits", credits),
        Route("/api/history", history),
        Route("/api/enhance/{job_id}", delete_job, methods=["DELETE"]),
    ]

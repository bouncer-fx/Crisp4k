import os
import httpx

def test_mode():
    return os.environ.get("TEST_MODE", "false").strip().lower() == "true"

def _h(key):
    return {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json"}

async def adjust(url, key, user_id, delta):
    q = url + "/rest/v1/credits?user_id=eq." + user_id
    async with httpx.AsyncClient(timeout=15) as c:
        for _ in range(3):
            r = await c.get(q + "&select=available_credits", headers=_h(key))
            rows = r.json() if r.status_code == 200 else []
            if not rows:
                return False, "No credit account found."
            bal = rows[0]["available_credits"]
            if bal + delta < 0:
                return False, "Not enough credits. You need %d, you have %d." % (-delta, bal)
            u = await c.patch(q + "&available_credits=eq." + str(bal),
                headers={**_h(key), "Prefer": "return=representation"},
                json={"available_credits": bal + delta})
            if u.status_code == 200 and u.json():
                return True, None
    return False, "Could not update credits. Try again."

const C = window.CRISP_CONFIG;
const H = { apikey: C.SUPABASE_KEY, "Content-Type": "application/json" };
const $ = (id) => document.getElementById(id);
const say = (t) => { $("out").textContent = t; };

async function call(path, body) {
  const r = await fetch(C.SUPABASE_URL + "/auth/v1/" + path, {
    method: "POST", headers: H, body: JSON.stringify(body)
  });
  let data = {};
  try { data = await r.json(); } catch (e) {}
  return { ok: r.ok, data: data };
}

function saveSession(d) {
  localStorage.setItem("crisp_session", JSON.stringify({
    access_token: d.access_token,
    refresh_token: d.refresh_token,
    email: d.user.email
  }));
}

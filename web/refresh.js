(function () {
  var C = window.CRISP_CONFIG;
  function load() { return JSON.parse(localStorage.getItem("crisp_session") || "null"); }
  function exp(t) { try { return JSON.parse(atob(t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))).exp; } catch (e) { return 0; } }
  function refresh() {
    var s = load();
    if (!s || !s.refresh_token) return;
    if (exp(s.access_token) > Date.now() / 1000 + 120) return;
    try {
      var x = new XMLHttpRequest();
      x.open("POST", C.SUPABASE_URL + "/auth/v1/token?grant_type=refresh_token", false);
      x.setRequestHeader("apikey", C.SUPABASE_KEY);
      x.setRequestHeader("Content-Type", "application/json");
      x.send(JSON.stringify({ refresh_token: s.refresh_token }));
      if (x.status === 200) {
        var d = JSON.parse(x.responseText);
        localStorage.setItem("crisp_session", JSON.stringify({ access_token: d.access_token, refresh_token: d.refresh_token, email: s.email }));
      } else if (x.status === 400 || x.status === 401) { localStorage.removeItem("crisp_session"); }
    } catch (e) {}
  }
  refresh();
  setInterval(refresh, 5 * 60 * 1000);
})();

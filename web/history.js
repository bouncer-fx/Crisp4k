(function () {
  var C = window.CRISP_CONFIG;
  var s = JSON.parse(localStorage.getItem("crisp_session") || "null");
  if (!s) { location.href = "login.html"; return; }
  var H = { Authorization: "Bearer " + s.access_token };
  var list = document.getElementById("list"), note = document.getElementById("note");
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x !== undefined) e.textContent = x; return e; }

  function card(it) {
    var d = el("div", "card hist");
    if (it.enhanced_url) { var im = el("img"); im.src = it.preview_url || it.enhanced_url; im.alt = "Enhanced"; d.appendChild(im); }
    d.appendChild(el("p", "", it.enhancement_mode.toUpperCase() + " | " + it.status));
    d.appendChild(el("p", "muted", new Date(it.created_at).toLocaleString() + (it.processing_time ? " | " + it.processing_time + "s" : "")));
    var row = el("div", "row");
    if (it.enhanced_url) { var a = el("a", "btn", "Download"); a.href = it.enhanced_url + (it.enhanced_url.indexOf("?") > -1 ? "&" : "?") + "download=crisp4k-enhanced.jpg"; a.target = "_blank"; row.appendChild(a); }
    var del = el("button", "", "Delete");
    del.onclick = function () {
      if (!confirm("Delete this photo and its enhancement permanently?")) return;
      fetch(C.API_URL + "/api/enhance/" + it.id, { method: "DELETE", headers: H })
        .then(function (r) { if (r.ok) d.remove(); else alert("Could not delete."); });
    };
    row.appendChild(del);
    d.appendChild(row);
    return d;
  }

  fetch(C.API_URL + "/api/history", { headers: H })
    .then(function (r) {
      if (r.status === 401) { localStorage.removeItem("crisp_session"); location.href = "login.html"; throw 0; }
      return r.json();
    })
    .then(function (d) {
      note.textContent = d.items.length ? "Your last " + d.items.length + " photos." : "No enhancements yet.";
      d.items.forEach(function (it) { list.appendChild(card(it)); });
    })
    .catch(function () { if (!list.children.length) note.textContent = "Could not load history."; });
})();

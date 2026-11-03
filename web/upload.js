(function () {
  var fileInput = document.getElementById("file");
  var btn = document.getElementById("btn-upload");
  var thread = document.getElementById("thread");
  var C = window.CRISP_CONFIG;
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  function session() { return JSON.parse(localStorage.getItem("crisp_session") || "null"); }

  function slider(box, orig, enh) {
    box.className = "compare";
    box.innerHTML = '<img class="base" src="' + enh + '" alt="Enhanced">' +
      '<div class="top"><img src="' + orig + '" alt="Original"></div>' +
      '<div class="bar"></div><div class="knob">&lt;&gt;</div>' +
      '<span class="lbl l1">ORIGINAL</span><span class="lbl l2">CRISP4K ENHANCED</span>';
    var top = box.querySelector(".top"), bar = box.querySelector(".bar");
    var knob = box.querySelector(".knob"), base = box.querySelector(".base");
    var setW = function () { top.firstChild.style.setProperty("--w", base.clientWidth + "px"); };
    base.addEventListener("load", setW);
    window.addEventListener("resize", setW);
    var move = function (x) {
      var r = box.getBoundingClientRect();
      var p = Math.min(100, Math.max(0, ((x - r.left) / r.width) * 100));
      top.style.width = p + "%"; bar.style.left = p + "%"; knob.style.left = p + "%";
    };
    var drag = false;
    box.onpointerdown = function (e) { drag = true; box.setPointerCapture(e.pointerId); move(e.clientX); };
    box.onpointermove = function (e) { if (drag) move(e.clientX); };
    box.onpointerup = function () { drag = false; };
  }

  fileInput.addEventListener("change", function () {
    var f = fileInput.files[0];
    var msg = document.getElementById("msg");
    if (!f) return;
    if (f.size > 5 * 1024 * 1024) { msg.textContent = "Photo is over 5 MB. Please choose a smaller one."; return; }
    msg.textContent = "";
    btn.onclick();
  });

  btn.onclick = async function () {
    var s = session(), f = fileInput.files[0];
    var mode = document.getElementById("mode").value;
    if (!s) { alert("Please log in first."); fileInput.value = ""; return; }
    if (!f) return;
    var u = document.createElement("div");
    u.className = "msg user";
    var im = document.createElement("img");
    im.src = URL.createObjectURL(f);
    var cap = document.createElement("p");
    cap.textContent = mode.toUpperCase() + " enhance";
    u.appendChild(im); u.appendChild(cap);
    var b = document.createElement("div");
    b.className = "msg bot";
    b.innerHTML = '<p class="muted">Enhancing your photo <span class="dots"><i></i><i></i><i></i></span></p>';
    thread.appendChild(u); thread.appendChild(b);
    b.scrollIntoView({ behavior: "smooth", block: "end" });
    var fd = new FormData();
    fd.append("file", f); fd.append("mode", mode);
    fileInput.value = "";
    var fail = function (t) { b.innerHTML = '<p class="muted">' + t + '</p>'; };
    try {
      var H = { Authorization: "Bearer " + s.access_token };
      var r = await fetch(C.API_URL + "/api/upload", { method: "POST", headers: H, body: fd });
      var d = await r.json();
      if (!r.ok) { fail(d.error || "Upload failed."); return; }
      var nh = "";
      if (d.notes && d.notes.length) {
        nh = '<ul class="notes"><li>' + d.notes.join("</li><li>") + "</li></ul>";
        b.innerHTML = '<p class="muted">I looked at your photo and chose these adjustments:</p>' + nh;
      }
      var shown = false;
      for (var i = 0; i < 400; i++) {
        await sleep(shown ? 1500 : 600);
        var q = await (await fetch(C.API_URL + "/api/enhance/" + d.id, { headers: H })).json();
        if (q.status === "FAILED") { fail("Enhancement failed. Please try again."); return; }
        if (q.preview_url && !shown) {
          shown = true;
          b.innerHTML = '<p class="muted">Preview ready. Preparing your full-size version <span class="dots"><i></i><i></i><i></i></span></p><div class="slot"></div>' + nh;
          slider(b.querySelector(".slot"), q.original_url, q.preview_url);
          b.scrollIntoView({ behavior: "smooth", block: "end" });
        }
        if (q.status === "COMPLETED") {
          var n = b.querySelector("p.muted");
          if (n) n.textContent = "Done. Drag the handle to compare.";
          var dl = document.createElement("a");
          dl.className = "btn";
          dl.textContent = "Download full-size";
          dl.href = q.enhanced_url + (q.enhanced_url.indexOf("?") > -1 ? "&" : "?") + "download=crisp4k-enhanced.jpg";
          dl.style.cssText = "display:inline-block;margin-top:14px";
          b.appendChild(dl);
          return;
        }
      }
      fail("This is taking too long. Check History later.");
    } catch (e) { fail("Could not reach the server."); }
  };
})();

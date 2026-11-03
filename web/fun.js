(function () {
  var thread = document.getElementById("thread");
  if (!thread) return;
  var st = document.createElement("style");
  st.textContent = ".cf{position:fixed;top:-14px;width:10px;height:14px;z-index:50;pointer-events:none;border-radius:2px;animation:cfall linear forwards}@keyframes cfall{to{transform:translateY(105vh) rotate(720deg)}}";
  document.head.appendChild(st);
  var COLORS = ["#ff6a13", "#0b4a1f", "#a6e3a1", "#ffd9b8", "#2f7bff"];
  var MSGS = ["Reading every pixel", "Looking at your light and colour", "Choosing the right adjustments", "Polishing the details", "Almost there"];

  function confetti() {
    for (var i = 0; i < 60; i++) {
      var c = document.createElement("div");
      c.className = "cf";
      c.style.left = Math.random() * 100 + "vw";
      c.style.background = COLORS[i % COLORS.length];
      c.style.animationDuration = (1.6 + Math.random() * 1.6) + "s";
      c.style.animationDelay = (Math.random() * 0.4) + "s";
      document.body.appendChild(c);
      setTimeout((function (el) { return function () { el.remove(); }; })(c), 4200);
    }
    if (navigator.vibrate) navigator.vibrate([40, 30, 60]);
  }

  function cycle(p) {
    var i = 0, last = null;
    var t = setInterval(function () {
      var n = p.firstChild;
      if (!p.isConnected || !n || (last !== null && n.nodeValue !== last)) { clearInterval(t); return; }
      i = (i + 1) % MSGS.length;
      last = MSGS[i] + " ";
      n.nodeValue = last;
    }, 1800);
  }

  function sweep(box) {
    var top = box.querySelector(".top"), bar = box.querySelector(".bar"), knob = box.querySelector(".knob");
    if (!top || !bar || !knob) return;
    var t0 = null;
    function set(v) { top.style.width = v + "%"; bar.style.left = v + "%"; knob.style.left = v + "%"; }
    set(92);
    function step(ts) {
      if (t0 === null) t0 = ts;
      var k = Math.min(1, (ts - t0) / 1000);
      set(92 - 42 * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function addShare(a) {
    if (!navigator.share) return;
    var b = document.createElement("button");
    b.textContent = "Share";
    b.style.cssText = "margin:14px 0 0 10px";
    b.onclick = async function () {
      var url = a.href.replace(/[?&]download=[^&]*/, "");
      try {
        var r = await fetch(url);
        var blob = await r.blob();
        var f = new File([blob], "crisp4k-enhanced.jpg", { type: "image/jpeg" });
        if (navigator.canShare && navigator.canShare({ files: [f] })) {
          await navigator.share({ files: [f], title: "Enhanced with CRISP4K" });
          return;
        }
      } catch (e) {}
      try { await navigator.share({ title: "CRISP4K", text: "Try CRISP4K - Your Picture. Just Better.", url: location.origin }); } catch (e) {}
    };
    a.parentNode.appendChild(b);
  }

  new MutationObserver(function (muts) {
    muts.forEach(function (m) {
      if (m.type === "attributes") {
        var t = m.target;
        if (t.classList && t.classList.contains("compare") && !t.dataset.swept) { t.dataset.swept = "1"; sweep(t); }
        return;
      }
      m.addedNodes.forEach(function (n) {
        if (n.nodeType !== 1) return;
        if (n.matches && n.matches(".msg.bot")) {
          var p = n.querySelector("p.muted");
          if (p && p.firstChild && /^Enhancing/.test(p.firstChild.nodeValue || "")) cycle(p);
        }
        if (n.tagName === "A" && /Download full-size/.test(n.textContent)) { addShare(n); confetti(); }
      });
    });
  }).observe(thread, { childList: true, subtree: true, attributes: true, attributeFilter: ["class"] });

  var input = document.getElementById("file");
  ["dragover", "drop"].forEach(function (ev) {
    document.addEventListener(ev, function (e) {
      e.preventDefault();
      if (ev === "drop" && input && e.dataTransfer && e.dataTransfer.files[0]) {
        try {
          var dt = new DataTransfer();
          dt.items.add(e.dataTransfer.files[0]);
          input.files = dt.files;
          input.dispatchEvent(new Event("change"));
        } catch (err) {}
      }
    });
  });
})();

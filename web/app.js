const MAX_MB = 10;
const OK = ["image/jpeg", "image/png", "image/webp"];
const file = document.getElementById("file");
const msg = document.getElementById("msg");
const preview = document.getElementById("preview");

file.addEventListener("change", () => {
  const f = file.files[0];
  preview.hidden = true;
  msg.textContent = "";
  if (!f) return;
  if (!OK.includes(f.type)) { msg.textContent = "Please choose a JPG, PNG or WEBP image."; return; }
  if (f.size > MAX_MB * 1024 * 1024) { msg.textContent = "File is too large. Maximum is " + MAX_MB + " MB."; return; }
  preview.src = URL.createObjectURL(f);
  preview.hidden = false;
  msg.textContent = f.name + " (" + (f.size / 1024 / 1024).toFixed(2) + " MB)";
});

const cmp = document.getElementById("compare");
function buildCompare(src) {
  cmp.innerHTML =
    '<img class="base" src="' + src + '" alt="Enhanced demo" style="filter:contrast(1.15) saturate(1.2)">' +
    '<div class="top"><img src="' + src + '" alt="Original"></div>' +
    '<div class="bar"></div><div class="knob">&lt;&gt;</div>' +
    '<span class="lbl l1">ORIGINAL</span><span class="lbl l2">CRISP4K ENHANCED</span>';
  cmp.hidden = false;
  const top = cmp.querySelector(".top");
  const bar = cmp.querySelector(".bar");
  const knob = cmp.querySelector(".knob");
  const base = cmp.querySelector(".base");
  const setW = () => top.firstChild.style.setProperty("--w", base.clientWidth + "px");
  base.addEventListener("load", setW);
  window.addEventListener("resize", setW);
  const move = (x) => {
    const r = cmp.getBoundingClientRect();
    const p = Math.min(100, Math.max(0, ((x - r.left) / r.width) * 100));
    top.style.width = p + "%";
    bar.style.left = p + "%";
    knob.style.left = p + "%";
  };
  let drag = false;
  cmp.onpointerdown = (e) => { drag = true; cmp.setPointerCapture(e.pointerId); move(e.clientX); };
  cmp.onpointermove = (e) => { if (drag) move(e.clientX); };
  cmp.onpointerup = () => { drag = false; };
}
file.addEventListener("change", () => {
  cmp.hidden = true;
  if (!preview.hidden) buildCompare(preview.src);
});

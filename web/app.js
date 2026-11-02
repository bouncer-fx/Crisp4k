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

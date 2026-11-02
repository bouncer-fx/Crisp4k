(function () {
  var fileInput = document.getElementById("file");
  var btn = document.getElementById("btn-upload");
  var out = document.getElementById("upmsg");
  var C = window.CRISP_CONFIG;

  function session() {
    return JSON.parse(localStorage.getItem("crisp_session") || "null");
  }

  fileInput.addEventListener("change", function () {
    out.textContent = "";
    btn.hidden = !(fileInput.files[0] && fileInput.files[0].size <= 10 * 1024 * 1024);
  });

  btn.onclick = async function () {
    var s = session();
    if (!s) { out.textContent = "Please log in first."; return; }
    var f = fileInput.files[0];
    if (!f) { out.textContent = "Choose a photo first."; return; }
    var fd = new FormData();
    fd.append("file", f);
    fd.append("mode", document.getElementById("mode").value);
    out.textContent = "Uploading...";
    try {
      var r = await fetch(C.API_URL + "/api/upload", {
        method: "POST",
        headers: { Authorization: "Bearer " + s.access_token },
        body: fd
      });
      var d = await r.json();
      out.textContent = r.ok ? "Uploaded. Job " + d.id + " is " + d.status + "." : (d.error || "Upload failed.");
    } catch (e) {
      out.textContent = "Could not reach the server.";
    }
  };
})();

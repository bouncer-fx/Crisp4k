(function () {
  var box = document.getElementById("authlinks");
  if (!box) return;
  var s = JSON.parse(localStorage.getItem("crisp_session") || "null");
  if (!s) {
    box.innerHTML = '<a href="login.html">Log in</a><a href="register.html">Register</a>';
    return;
  }
  box.innerHTML = '<span id="cred" class="muted"></span><a href="history.html">History</a><a href="#" id="logout">Log out</a>';
  document.getElementById("logout").onclick = function (e) {
    e.preventDefault();
    localStorage.removeItem("crisp_session");
    location.reload();
  };
  fetch(window.CRISP_CONFIG.API_URL + "/api/credits", { headers: { Authorization: "Bearer " + s.access_token } })
    .then(function (r) {
      if (r.status === 401) { localStorage.removeItem("crisp_session"); location.reload(); throw 0; }
      return r.json();
    })
    .then(function (d) { document.getElementById("cred").textContent = d.credits + " credits"; })
    .catch(function () {});
})();

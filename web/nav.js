(function () {
  var box = document.getElementById("authlinks");
  if (!box) return;
  var s = JSON.parse(localStorage.getItem("crisp_session") || "null");
  if (s) {
    box.innerHTML = '<a href="#" id="logout">Log out</a>';
    document.getElementById("logout").onclick = function (e) {
      e.preventDefault();
      localStorage.removeItem("crisp_session");
      location.reload();
    };
  } else {
    box.innerHTML = '<a href="login.html">Log in</a><a href="register.html">Register</a>';
  }
})();

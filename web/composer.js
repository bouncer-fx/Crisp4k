(function () {
  var bar = document.querySelector(".composer");
  var f = document.getElementById("file");
  var hero = document.querySelector(".hero .btn");
  if (hero) hero.onclick = function (e) { e.preventDefault(); f.click(); };
  var vv = window.visualViewport;
  function lift() {
    if (!vv) return;
    var o = window.innerHeight - vv.height - vv.offsetTop;
    bar.style.bottom = Math.max(0, o) + "px";
  }
  if (vv) { vv.addEventListener("resize", lift); vv.addEventListener("scroll", lift); }
})();

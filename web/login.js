$("btn-login").onclick = async () => {
  say("Logging in...");
  const r = await call("token?grant_type=password", {
    email: $("email").value.trim(), password: $("pass").value
  });
  if (!r.ok) { say(r.data.error_description || r.data.msg || "Login failed."); return; }
  saveSession(r.data);
  window.location.href = "index.html";
};

$("btn-recover").onclick = async (e) => {
  e.preventDefault();
  const email = $("email").value.trim();
  if (!email) { say("Type your email first."); return; }
  await call("recover", { email: email });
  say("If that email has an account, a reset link is on its way.");
};

$("btn-register").onclick = async () => {
  const email = $("email").value.trim(), password = $("pass").value;
  if (password.length < 8) { say("Password must be at least 8 characters."); return; }
  say("Creating account...");
  const r = await call("signup", { email: email, password: password });
  if (!r.ok) { say(r.data.msg || r.data.error_description || "Registration failed."); return; }
  if (r.data.access_token) {
    saveSession(r.data);
    window.location.href = "index.html";
  } else {
    say("Account created. Check your email to confirm it, then log in.");
  }
};

// handles sign-up & login
const signupForm = document.getElementById("signupForm");
const loginForm  = document.getElementById("loginForm");

function attach(endpoint, form) {
  form?.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(form));
    const res = await fetch(`/api/auth/${endpoint}`, {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(payload)
    });

    if (res.ok) {
      const { access_token } = await res.json();
      localStorage.setItem("token", access_token);
      window.location.href = "dashboard.html";
    } else alert("Authentication failed");
  });
}

attach("signup", signupForm);
attach("login",  loginForm);

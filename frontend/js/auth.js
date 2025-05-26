const API = '/api/auth';
function saveToken(t) { localStorage.setItem('token', t); }
function getToken()   { return localStorage.getItem('token'); }
window.getToken = getToken;

window.bindLoginForm = function () {
  const form = document.getElementById('loginForm');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(form).entries());
    const res  = await fetch(`${API}/login`, {
      method: 'POST', headers: { 'Content-Type':'application/json' },
      body: JSON.stringify(body)
    });
    if (res.ok) {
      saveToken((await res.json()).access_token);
      window.location = 'app.html';
    } else alert('Login failed');
  });
};

window.bindSignupForm = function () {
  const form = document.getElementById('signupForm');
  if (!form) return;
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(form).entries());
    const res  = await fetch(`${API}/signup`, {
      method: 'POST', headers: { 'Content-Type':'application/json' },
      body: JSON.stringify(body)
    });
    if (res.ok) {
      saveToken((await res.json()).access_token);
      window.location = 'app.html';
    } else alert('Signup failed');
  });
};

document.getElementById('logoutBtn')?.addEventListener('click', () => {
  saveToken('');
  window.location = 'index.html';
});

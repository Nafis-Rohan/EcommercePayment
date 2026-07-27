const registerForm = document.getElementById('register-form');
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const res = await fetch(API_BASE_URL + '/users/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
      body: JSON.stringify({
        email: form.get('email'),
        username: form.get('username'),
        password: form.get('password'),
        password_confirm: form.get('password2'),
      }),
    });
    const data = await res.json();
    if (res.ok) {
      setTokens(data.access, data.refresh);
      window.location.href = 'index.html';
    } else {
      document.getElementById('message').textContent = JSON.stringify(data);
    }
  });
}

const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const res = await fetch(API_BASE_URL + '/users/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
      body: JSON.stringify({
        email: form.get('email'),
        password: form.get('password'),
      }),
    });
    const data = await res.json();
    if (res.ok) {
      setTokens(data.access, data.refresh);
      window.location.href = 'index.html';
    } else {
      document.getElementById('message').textContent = JSON.stringify(data);
    }
  });
}

renderNav();

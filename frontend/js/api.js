// Thin fetch wrapper: attaches the JWT, and retries once via refresh on a 401.

function getAccessToken() { return localStorage.getItem('access_token'); }
function getRefreshToken() { return localStorage.getItem('refresh_token'); }

function setTokens(access, refresh) {
  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function tryRefreshToken() {
  try {
    const res = await fetch(API_BASE_URL + '/users/login/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: getRefreshToken() }),
    });
    if (!res.ok) { clearTokens(); return false; }
    const data = await res.json();
    setTokens(data.access, data.refresh);
    return true;
  } catch (e) {
    clearTokens();
    return false;
  }
}

async function apiFetch(path, options = {}) {
  options.headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    options.headers['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) options.headers['Authorization'] = 'Bearer ' + token;

  let res = await fetch(API_BASE_URL + path, options);

  if (res.status === 401 && getRefreshToken()) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      options.headers['Authorization'] = 'Bearer ' + getAccessToken();
      res = await fetch(API_BASE_URL + path, options);
    }
  }
  return res;
}

function requireAuth() {
  if (!getAccessToken()) window.location.href = 'login.html';
}

async function logout() {
  try {
    await apiFetch('/users/logout/', {
      method: 'POST',
      body: JSON.stringify({ refresh: getRefreshToken() }),
    });
  } catch (e) { /* ignore, we're clearing local state either way */ }
  clearTokens();
  clearCart();
  window.location.href = 'login.html';
}

function renderNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;
  const loggedIn = !!getAccessToken();
  nav.innerHTML = loggedIn
    ? `<a href="index.html">Products</a>
       <a href="cart.html">Cart (<span id="cart-count">0</span>)</a>
       <a href="orders.html">My Orders</a>
       <a href="profile.html">Profile</a>
       <a href="#" id="logout-link">Logout</a>`
    : `<a href="index.html">Products</a>
       <a href="login.html">Login</a>
       <a href="register.html">Register</a>`;

  const logoutLink = document.getElementById('logout-link');
  if (logoutLink) logoutLink.addEventListener('click', (e) => { e.preventDefault(); logout(); });

  updateCartCount();
}

requireAuth();
renderNav();

async function loadProfile() {
  const res = await apiFetch('/users/me/');
  const user = await res.json();
  document.querySelector('[name=first_name]').value = user.first_name || '';
  document.querySelector('[name=last_name]').value = user.last_name || '';
}

document.getElementById('profile-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const res = await apiFetch('/users/me/', {
    method: 'PATCH',
    body: JSON.stringify({
      first_name: form.get('first_name'),
      last_name: form.get('last_name'),
    }),
  });
  const data = await res.json();
  document.getElementById('message').textContent = res.ok ? 'Updated!' : JSON.stringify(data);
});

loadProfile();

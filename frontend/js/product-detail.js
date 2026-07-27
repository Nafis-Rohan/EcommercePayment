const productId = new URLSearchParams(window.location.search).get('id');

async function loadProduct() {
  const res = await apiFetch(`/products/${productId}/`);
  const p = await res.json();
  document.getElementById('product').innerHTML = `
    <h1>${p.name}</h1>
    <p>${p.description || ''}</p>
    <p>Price: $${p.price}</p>
    <p>Stock: ${p.stock}</p>
  `;
}

async function loadRecommendations() {
  const res = await apiFetch(`/products/${productId}/recommendations/`);
  const items = await res.json();
  document.getElementById('recommendations').innerHTML = items.map(p => `
    <div class="card"><a href="product.html?id=${p.id}">${p.name}</a> — $${p.price}</div>
  `).join('') || '<p>No related products.</p>';
}

document.getElementById('add-to-cart').addEventListener('click', () => {
  if (!getAccessToken()) {
    window.location.href = 'login.html';
    return;
  }
  const qty = parseInt(document.getElementById('qty').value, 10) || 1;
  addToCart(productId, qty);
  alert('Added to cart');
});

renderNav();
loadProduct();
loadRecommendations();

async function loadProducts() {
  const res = await apiFetch('/products/');
  const products = await res.json();
  document.getElementById('products').innerHTML = products.map(p => `
    <div class="card">
      <a href="product.html?id=${p.id}"><strong>${p.name}</strong></a>
      — $${p.price} (stock: ${p.stock}, ${p.status})
    </div>
  `).join('');
}

async function loadCategoryTree() {
  const res = await apiFetch('/products/categories/tree/');
  const tree = await res.json();
  document.getElementById('categories').innerHTML =
    '<h3>Categories</h3><pre>' + JSON.stringify(tree, null, 2) + '</pre>';
}

renderNav();
loadProducts();
loadCategoryTree();

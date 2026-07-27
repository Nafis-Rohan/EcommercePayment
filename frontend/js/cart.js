// Client-side cart, just localStorage — the server is the source of truth for
// totals/stock once an order is actually created (see plan.md: totals are always
// recomputed server-side, never trusted from the client).

function getCart() {
  return JSON.parse(localStorage.getItem('cart') || '[]');
}

function saveCart(cart) {
  localStorage.setItem('cart', JSON.stringify(cart));
  updateCartCount();
}

function clearCart() {
  localStorage.removeItem('cart');
  updateCartCount();
}

function addToCart(productId, quantity) {
  const cart = getCart();
  const existing = cart.find(i => i.product_id === productId);
  if (existing) existing.quantity += quantity;
  else cart.push({ product_id: productId, quantity });
  saveCart(cart);
}

function removeFromCart(productId) {
  saveCart(getCart().filter(i => i.product_id !== productId));
}

function updateCartCount() {
  const el = document.getElementById('cart-count');
  if (el) el.textContent = getCart().reduce((n, i) => n + i.quantity, 0);
}

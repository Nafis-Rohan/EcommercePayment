requireAuth();
renderNav();

async function loadOrders() {
  const res = await apiFetch('/orders/');
  const orders = await res.json();
  document.getElementById('orders').innerHTML = orders.map(o => `
    <div class="card">
      <strong>Order ${o.id}</strong> — status: ${o.status} — total: $${o.total_amount}
      <ul>${o.items.map(i => `<li>product ${i.product} × ${i.quantity} = $${i.subtotal}</li>`).join('')}</ul>
    </div>
  `).join('') || '<p>No orders yet.</p>';
}

loadOrders();

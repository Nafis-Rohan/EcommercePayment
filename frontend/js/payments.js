requireAuth();
renderNav();

let stripe, cardElement, currentOrderId;

async function renderCart() {
  const cart = getCart();
  const container = document.getElementById('cart-items');
  if (cart.length === 0) {
    container.innerHTML = '<p>Cart is empty.</p>';
    document.getElementById('cart-total').textContent = '0.00';
    return;
  }

  const products = await Promise.all(
    cart.map(item => apiFetch(`/products/${item.product_id}/`).then(r => r.json()))
  );

  let total = 0;
  container.innerHTML = cart.map((item, i) => {
    const p = products[i];
    const lineTotal = p.price * item.quantity;
    total += lineTotal;
    return `
      <div class="card">
        ${p.name} — qty ${item.quantity} — $${p.price} each — $${lineTotal.toFixed(2)}
        <button onclick="removeFromCart('${item.product_id}'); renderCart();">Remove</button>
      </div>
    `;
  }).join('');
  document.getElementById('cart-total').textContent = total.toFixed(2);
}

document.getElementById('place-order-btn').addEventListener('click', async () => {
  const cart = getCart();
  if (cart.length === 0) { alert('Cart is empty'); return; }

  const res = await apiFetch('/orders/', {
    method: 'POST',
    body: JSON.stringify({
      items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity })),
    }),
  });
  const data = await res.json();
  if (!res.ok) { alert('Order failed: ' + JSON.stringify(data)); return; }

  clearCart();
  renderCart();
  currentOrderId = data.id;
  document.getElementById('order-id').textContent = currentOrderId;
  document.getElementById('order-section').style.display = 'block';
});

document.getElementById('pay-bkash-btn').addEventListener('click', async () => {
  const res = await apiFetch('/payments/checkout/', {
    method: 'POST',
    body: JSON.stringify({ order_id: currentOrderId, provider: 'bkash' }),
  });
  const data = await res.json();
  if (!res.ok) { alert('Checkout failed: ' + JSON.stringify(data)); return; }
  // bKash's flow needs a human on their hosted page, so we hand off the whole
  // browser tab to them; they redirect back to the backend's callback URL when done.
  window.location.href = data.bkash_url;
});

document.getElementById('pay-stripe-btn').addEventListener('click', async () => {
  const res = await apiFetch('/payments/checkout/', {
    method: 'POST',
    body: JSON.stringify({ order_id: currentOrderId, provider: 'stripe' }),
  });
  const data = await res.json();
  if (!res.ok) { alert('Checkout failed: ' + JSON.stringify(data)); return; }

  document.getElementById('stripe-section').style.display = 'block';
  stripe = Stripe(STRIPE_PUBLISHABLE_KEY);
  cardElement = stripe.elements().create('card');
  cardElement.mount('#card-element');

  document.getElementById('confirm-stripe-btn').onclick = async () => {
    const msgEl = document.getElementById('stripe-message');
    msgEl.textContent = 'Processing...';
    // This confirmCardPayment call is the real, production version of the
    // `stripe payment_intents confirm ...` CLI command used during API-only
    // testing — a live card field replaces the manual step entirely.
    const result = await stripe.confirmCardPayment(data.client_secret, {
      payment_method: { card: cardElement },
    });
    if (result.error) {
      msgEl.textContent = 'Payment failed: ' + result.error.message;
    } else if (result.paymentIntent.status === 'succeeded') {
      msgEl.textContent = 'Payment succeeded! Check "My Orders" in a moment (webhook needs to arrive).';
    }
  };
});

renderCart();

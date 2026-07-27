# Payment Flow — Stripe (backend flow)

```mermaid
sequenceDiagram
    participant Backend
    participant Stripe

    Backend->>Stripe: Create a payment
    Stripe-->>Backend: Payment details
    Backend->>Backend: Save payment (Pending)

    Stripe->>Backend: "Payment succeeded" ✅
    Backend->>Backend: Verify it's really from Stripe
    Backend->>Backend: Reduce stock
    Backend->>Backend: Mark payment Success, order Paid
```

**In plain words:** the backend asks Stripe to start a payment and saves it as
Pending. Later, Stripe notifies the backend the payment succeeded; the backend
checks that notification is genuine, then reduces stock and marks the order Paid.

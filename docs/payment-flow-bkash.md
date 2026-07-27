# Payment Flow — bKash (backend flow)

```mermaid
sequenceDiagram
    participant Backend
    participant bKash

    Backend->>bKash: Get access token
    bKash-->>Backend: Token
    Backend->>bKash: Create a payment
    bKash-->>Backend: Payment link + ID
    Backend->>Backend: Save payment (Pending)

    bKash->>Backend: User approved/declined it
    alt approved
        Backend->>bKash: Confirm the payment
        bKash-->>Backend: Confirmed ✅
        Backend->>Backend: Reduce stock
        Backend->>Backend: Mark payment Success, order Paid
    else declined
        Backend->>Backend: Mark payment Failed, order Cancelled
    end
```

**In plain words:** the backend logs into bKash and starts a payment, saving it as
Pending. Once bKash reports whether the user approved or declined it, the backend
either confirms the payment and marks the order Paid, or marks it Failed/Cancelled.

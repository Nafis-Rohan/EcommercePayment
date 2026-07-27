from abc import ABC, abstractmethod


class PaymentStrategy(ABC):
    """Common interface every payment provider must implement."""

    def __init__(self, payment):
        self.payment = payment

    @abstractmethod
    def initiate(self, **kwargs):
        """Start a payment with the provider. Returns data the client needs (e.g. client_secret, redirect URL)."""
        raise NotImplementedError

    @abstractmethod
    def confirm(self, **kwargs):
        """Confirm/execute a payment that the client has approved on the provider's side."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, **kwargs):
        """Verify a payment's status independently (webhook signature check, or a status query call)."""
        raise NotImplementedError

from abc import ABC, abstractmethod


class PaymentStrategy(ABC):

    def __init__(self, payment):
        self.payment = payment

    @abstractmethod
    def initiate(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def confirm(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def verify(self, **kwargs):
        raise NotImplementedError

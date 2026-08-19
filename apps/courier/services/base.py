from abc import ABC, abstractmethod


class BaseCourierClient(ABC):
    @abstractmethod
    def create_shipment(self, order):
        raise NotImplementedError

    @abstractmethod
    def get_status(self, shipment):
        raise NotImplementedError

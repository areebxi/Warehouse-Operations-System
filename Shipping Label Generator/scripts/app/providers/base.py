from __future__ import annotations

from abc import ABC, abstractmethod

from scripts.app.models.label import Label
from scripts.app.models.order import Order
from scripts.app.models.shipment import Shipment


class Provider(ABC):
    @abstractmethod
    async def lookup_orders(self, order_number: str) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def list_shipments(
        self,
        order_id: int,
        *,
        include_voided: bool,
        page_size: int | None = None,
    ) -> list[Shipment]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_label(self, shipment_id: int) -> Label | None:
        raise NotImplementedError

    @abstractmethod
    async def create_label(
        self,
        *,
        order: Order,
        carrier_code: str,
        service_code: str,
        package_code: str,
        ship_date: str,
        weight: float | None,
        weight_unit: str | None,
        customer_reference: str | None,
    ) -> Label:
        raise NotImplementedError

    @abstractmethod
    async def void_label(self, shipment_id: int) -> None:
        raise NotImplementedError

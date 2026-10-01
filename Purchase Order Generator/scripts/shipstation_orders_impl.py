"""ShipStationAPI class shell — methods live in mixin modules."""

from __future__ import annotations

from shared.shipstation import (
    ShipStationClient,
    ShipStationCredentials,
    load_shipstation_credentials,
)
from shipstation_orders_impl_mixin1 import ShipStationAPIMixin1
from shipstation_orders_impl_mixin2 import ShipStationAPIMixin2


class ShipStationAPI(ShipStationAPIMixin1, ShipStationAPIMixin2):
    """PO façade over shared ShipStationClient + local CSV/JSON export."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        *,
        base_url: str | None = None,
        client: ShipStationClient | None = None,
    ):
        if client is not None:
            self._client = client
        elif api_key and api_secret:
            creds = ShipStationCredentials(
                base_url=(base_url or "https://ssapi.shipstation.com").rstrip("/"),
                api_key=api_key,
                api_secret=api_secret,
            )
            self._client = ShipStationClient(creds)
        else:
            self._client = ShipStationClient(load_shipstation_credentials())
        self.api_key = self._client.credentials.api_key
        self.api_secret = self._client.credentials.api_secret
        self.base_url = self._client.credentials.base_url

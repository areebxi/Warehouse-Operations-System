"""ShipStationAPI CSV export method (delegates to shipstation_orders_export)."""

from __future__ import annotations

from shipstation_orders_export import export_orders_to_csv as _export_orders_to_csv


class ShipStationAPIMixin1Mixin1:
    def export_orders_to_csv(self, orders, filename=None):
        return _export_orders_to_csv(orders, filename)

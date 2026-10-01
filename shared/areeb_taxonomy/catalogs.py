"""In-memory BTC/Uneek indexes + classify_plain / classify_packs / classify_cl."""
from __future__ import annotations

from typing import Any, Mapping

from shared.areeb_taxonomy.cl_classify import cl_standard
from shared.areeb_taxonomy.consts import (
    BTC_SRC,
    SOURCE_BTC_SPC,
    SOURCE_BTC_UID,
    SOURCE_NONE,
    SOURCE_UNEEK_CODE,
    SOURCE_UNEEK_SHORT,
    UNEEK_SRC,
)
from shared.areeb_taxonomy.plain import plain_leftover
from shared.areeb_taxonomy.values import AreebValues, cell, coalesce_areeb, from_src_row, keyfold

class AreebCatalogs:
    """In-memory BTC + Uneek indexes (Plain / Packs only)."""

    def __init__(self) -> None:
        self.btc_by_uid: dict[str, dict[str, str]] = {}
        self.btc_by_spc: dict[str, dict[str, str]] = {}
        self.uneek_by_short: dict[str, dict[str, str]] = {}
        self.uneek_by_code: dict[str, dict[str, str]] = {}

    def btc_uid(self, sku: object) -> AreebValues:
        row = self.btc_by_uid.get(cell(sku)) or self.btc_by_uid.get(keyfold(sku))
        if not row:
            return AreebValues()
        return from_src_row(row, BTC_SRC, SOURCE_BTC_UID)

    def btc_spc(self, code: object) -> AreebValues:
        row = self.btc_by_spc.get(cell(code)) or self.btc_by_spc.get(keyfold(code))
        if not row:
            return AreebValues()
        return from_src_row(row, BTC_SRC, SOURCE_BTC_SPC)

    def uneek_short(self, code: object) -> AreebValues:
        k = cell(code)
        row = self.uneek_by_short.get(k) or self.uneek_by_short.get(k.casefold())
        if not row:
            return AreebValues()
        return from_src_row(row, UNEEK_SRC, SOURCE_UNEEK_SHORT)

    def uneek_product_code(self, code: object) -> AreebValues:
        k = cell(code)
        row = self.uneek_by_code.get(k) or self.uneek_by_code.get(k.casefold())
        if not row:
            return AreebValues()
        return from_src_row(row, UNEEK_SRC, SOURCE_UNEEK_CODE)

    def classify_plain(
        self,
        sku: object,
        product_code: object = "",
        brand: object = "",
        description: object = "",
    ) -> AreebValues:
        leftover = plain_leftover(brand=brand, description=description)
        hit = self.btc_uid(sku)
        if hit.any_filled():
            if hit.all_filled():
                return hit
            return coalesce_areeb(hit, leftover)
        hit = self.uneek_short(sku)
        if hit.any_filled():
            if hit.all_filled():
                return hit
            return coalesce_areeb(hit, leftover)
        hit = self.btc_spc(product_code)
        if hit.any_filled():
            if hit.all_filled():
                return hit
            return coalesce_areeb(hit, leftover)
        return leftover

    def classify_packs(
        self,
        *,
        item1_sku: object = "",
        product_code: object = "",
        channel_child_sku: object = "",
    ) -> AreebValues:
        hit = self.btc_uid(item1_sku)
        if hit.any_filled():
            return hit
        hit = self.btc_spc(product_code)
        if hit.any_filled():
            return hit
        for key in (channel_child_sku, item1_sku, product_code):
            hit = self.uneek_short(key)
            if hit.any_filled():
                return hit
            hit = self.uneek_product_code(key)
            if hit.any_filled():
                return hit
        return AreebValues()

    def classify_cl(self, row: Mapping[str, Any]) -> AreebValues:
        return cl_standard(row)

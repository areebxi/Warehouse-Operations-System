from __future__ import annotations

import argparse
import asyncio
import base64
import os
import sys
from typing import Any

import aiohttp
from dotenv import load_dotenv


def _basic_auth_header(key: str, secret: str) -> str:
    token = base64.b64encode(f"{key}:{secret}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


async def _get_shipments_by_tracking(
    *,
    session: aiohttp.ClientSession,
    base_url: str,
    tracking: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    url = f"{base_url}/shipments"
    async with session.get(url, params={"trackingNumber": tracking, "pageSize": int(page_size)}) as resp:
        text = await resp.text()
        if resp.status >= 400:
            raise RuntimeError(f"GET /shipments failed ({resp.status}): {text[:2000]}")
        try:
            data = await resp.json()
        except Exception as e:
            raise RuntimeError(f"Invalid JSON from GET /shipments: {text[:2000]}") from e

    # ShipStation style is typically {"shipments": [...], ...}
    if isinstance(data, dict) and isinstance(data.get("shipments"), list):
        return list(data["shipments"])
    if isinstance(data, list):
        return data
    return []


async def _void_shipment(
    *,
    session: aiohttp.ClientSession,
    base_url: str,
    shipment_id: int,
) -> tuple[bool, str]:
    url = f"{base_url}/shipments/voidlabel"
    async with session.post(url, json={"shipmentId": int(shipment_id)}) as resp:
        text = await resp.text()
        if 200 <= resp.status < 300:
            return True, text
        return False, text


async def _run(*, tracking: str) -> int:
    load_dotenv(override=False)

    key = _env("SHIPSTATION_API_KEY")
    secret = _env("SHIPSTATION_API_SECRET")
    base_url = _env("SHIPSTATION_API_BASE_URL") or "https://ssapi.shipstation.com"

    if not key or not secret:
        print("ERROR: Missing SHIPSTATION_API_KEY / SHIPSTATION_API_SECRET in environment or .env", file=sys.stderr)
        return 2

    tracking = str(tracking).strip()
    if not tracking:
        print("ERROR: tracking number is blank", file=sys.stderr)
        return 2

    headers = {
        "Authorization": _basic_auth_header(key, secret),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        shipments = await _get_shipments_by_tracking(session=session, base_url=base_url, tracking=tracking, page_size=50)

        if not shipments:
            print(f"No shipments found for trackingNumber={tracking}")
            return 0

        print(f"Found {len(shipments)} shipment(s) for trackingNumber={tracking}")

        any_failed = False
        for sh in shipments:
            if not isinstance(sh, dict):
                continue

            shipment_id = sh.get("shipmentId")
            voided = bool(sh.get("voided") or False)
            trk = sh.get("trackingNumber") or ""
            carrier = sh.get("carrierCode") or ""

            if shipment_id is None:
                print("Skipping shipment with missing shipmentId")
                continue

            try:
                sid = int(shipment_id)
            except Exception:
                print(f"Skipping shipment with non-int shipmentId={shipment_id!r}")
                continue

            print(f"- shipmentId={sid} carrierCode={carrier} trackingNumber={trk} voided={voided}")

            if voided:
                print("  already voided, skipping")
                continue

            ok, body = await _void_shipment(session=session, base_url=base_url, shipment_id=sid)
            if ok:
                print("  void SUCCESS")
            else:
                any_failed = True
                print(f"  void FAILED: {body[:2000]}")

        return 1 if any_failed else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="void_by_tracking", description="Void ShipStation labels by tracking number.")
    p.add_argument(
        "tracking",
        help="Tracking number to search shipments for (voids all non-voided shipments returned).",
    )
    args = p.parse_args(argv)
    return asyncio.run(_run(tracking=args.tracking))


if __name__ == "__main__":
    raise SystemExit(main())


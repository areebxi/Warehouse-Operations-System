"""Unit checks for shared ShipStation credential + listtags parsing (no network)."""

from __future__ import annotations

import pytest

from shared.shipstation.credentials import parse_credentials_text
from shared.shipstation.sync_client import parse_listtags_payload, parse_stores_payload


def test_parse_credentials_requires_real_api_keys():
    creds = parse_credentials_text(
        "REAL_API_BASE_URL=https://ssapi.shipstation.com\n"
        "REAL_API_KEY=abc\n"
        "REAL_API_SECRET=xyz\n"
    )
    assert creds.api_key == "abc"
    assert creds.api_secret == "xyz"
    assert creds.base_url == "https://ssapi.shipstation.com"


def test_parse_credentials_default_base_url():
    creds = parse_credentials_text("REAL_API_KEY=k\nREAL_API_SECRET=s\n")
    assert creds.api_key == "k"
    assert "ssapi.shipstation.com" in creds.base_url


def test_parse_listtags_wrapped_and_bare():
    wrapped = parse_listtags_payload(
        {"tags": [{"tagId": 2, "name": "Beta"}, {"tagId": 1, "name": "Alpha"}]}
    )
    assert [t["name"] for t in wrapped] == ["Alpha", "Beta"]
    bare = parse_listtags_payload([{"TagId": 9, "Name": "Zed"}])
    assert bare == [{"tagId": 9, "name": "Zed"}]


def test_parse_credentials_missing_raises():
    with pytest.raises(ValueError):
        parse_credentials_text("REAL_API_KEY=only\n")


def test_parse_stores_wrapped_and_bare():
    wrapped = parse_stores_payload(
        {
            "stores": [
                {"storeId": 2, "storeName": "MAS Clothing"},
                {"storeId": "1", "storeName": "Amazon UK"},
            ]
        }
    )
    assert wrapped == [
        {"storeId": 2, "storeName": "MAS Clothing"},
        {"storeId": 1, "storeName": "Amazon UK"},
    ]
    bare = parse_stores_payload([{"StoreId": 9, "StoreName": "Own"}])
    assert bare == [{"storeId": 9, "storeName": "Own"}]


def test_parse_stores_missing_raises():
    with pytest.raises(Exception) as exc:
        parse_stores_payload({"foo": 1})
    assert "stores" in str(exc.value).casefold()

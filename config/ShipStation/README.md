# config/ShipStation/

Single warehouse ShipStation Classic V1 secrets file.

Copy `.env.example` → `.env` and set:

```
REAL_API_BASE_URL=https://ssapi.shipstation.com
REAL_API_KEY=...
REAL_API_SECRET=...
```

Resolved by `shared.shipstation` via `shared.paths.shipstation_env_path()`.
Do not put API keys in Packing or Shipping config folders.

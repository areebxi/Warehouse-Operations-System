# config/

Shared machine-local secrets only.

App-owned GUI settings / YAML / FTP config live inside each app folder.
ShipStation API keys are the exception — one warehouse file for all apps.

| Folder | Contents |
|--------|----------|
| `ShipStation/` | Only place for ShipStation `REAL_API_*` (`.env`) |

Copy `ShipStation/.env.example` → `.env`. Do not commit live secrets.

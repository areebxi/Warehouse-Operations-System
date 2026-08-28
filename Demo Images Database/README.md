# Demo Images Database

Placeholder images for **offline testing** when UK design/apparel storage is unavailable.

| Folder | Role |
|--------|------|
| `Product Images/` | Apparel / product image slot |
| `Normal Designs/` | Normal logo/design folder |
| `Personalized Designs/Single Position/` | Customise single-position folder |
| `Personalized Designs/Double Position/` | Customise double-position folder |

Each folder holds `demo.png`. In the packing apps, check **Use demo images** — lookups treat missing files as found and PDFs embed these placeholders.

Resolve via `shared/paths.py` (`demo_*_dir` helpers).

import re
from pathlib import Path

NORMAL_LOGO_TOKEN_RE = re.compile(r"([0-9A-Za-z]+(?:LG|TSU|AV|HK))-[0-9A-Za-z]+")
FAWAD_LOGO_TOKEN_RE = re.compile(r"(fawad\d+)-[0-9A-Za-z]+", re.IGNORECASE)

REQUIRED_COLUMNS = [
    "Tags",
    "Order Number",
    "Item SKU",
    "Picture Name",
    "Customise",
    "Prime",
    "Apparel Image",
    "Logo/Design Image",
]

PRIME_TAG_EXACT = "Amazon Prime Order"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output"
PREFIX_STEP2 = "2_enrich_cl_lookup_"


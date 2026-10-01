"""Department / category / product-type / subcategory closed lists."""
from __future__ import annotations

DEFAULT_STYLE = "Standard"

DEPARTMENTS = (
    "Mens",
    "Womens",
    "Kids",
    "Unisex",
    "General",
)

# --- Category (Areeb) ---
CAT_TEE = "T-Shirts"
CAT_POLO = "Polo Shirts"
CAT_SWEAT = "Sweatshirts & Hoodies"
CAT_SHIRT = "Shirts"
CAT_JACKET = "Jackets"
CAT_FLEECE = "Fleeces"
CAT_GILET = "Gilets"
CAT_TROUSER = "Trousers"
CAT_SHORTS = "Shorts"
CAT_BABY = "Babywear"
CAT_HEALTH = "Healthcare"
CAT_HOSP = "Hospitality"
CAT_SAFETY = "Safetywear"
CAT_HEAD = "Headwear"
CAT_BAGS = "Bags"
CAT_SETS = "Sets"
CAT_STICKER = "Stickers"
CAT_IRON = "Iron-On"
CAT_MUGS = "Mugs"
CAT_ACC = "Accessories"

CATEGORIES = (
    CAT_TEE,
    CAT_POLO,
    CAT_SWEAT,
    CAT_SHIRT,
    CAT_JACKET,
    CAT_FLEECE,
    CAT_GILET,
    CAT_TROUSER,
    CAT_SHORTS,
    CAT_BABY,
    CAT_HEALTH,
    CAT_HOSP,
    CAT_SAFETY,
    CAT_HEAD,
    CAT_BAGS,
    CAT_SETS,
    CAT_STICKER,
    CAT_IRON,
    CAT_MUGS,
    CAT_ACC,
)

# --- Product Type (Areeb) — silhouette / bag kind, no gender ---
TYPE_SS_TEE = "Short Sleeve T-Shirt"
TYPE_LS_TEE = "Long Sleeve T-Shirt"
TYPE_TANK = "Tank Top"
TYPE_SS_POLO = "Short Sleeve Polo"
TYPE_LS_POLO = "Long Sleeve Polo"
TYPE_HOODIE = "Hoodie"
TYPE_ZIP_HOODIE = "Zip Hoodie"
TYPE_SWEAT = "Sweatshirt"
TYPE_SHIRT = "Shirt"
TYPE_RUGBY = "Rugby Shirt"
TYPE_JACKET = "Jacket"
TYPE_FLEECE = "Fleece"
TYPE_GILET = "Gilet"
TYPE_CARDIGAN = "Cardigan"
TYPE_TROUSER = "Trousers"
TYPE_CARGO = "Cargo Trousers"
TYPE_JOGGER = "Joggers"
TYPE_SHORTS = "Shorts"
TYPE_BODY = "Body Suit"
TYPE_ROMPER = "Romper"
TYPE_BABY_TEE = "Baby T-Shirt"
TYPE_TUTU = "Tutu"
TYPE_TUNIC = "Tunic"
TYPE_TABARD = "Tabard"
TYPE_SCRUB = "Scrub"
TYPE_APRON = "Apron"
TYPE_HV_TEE = "Hi-Vis T-Shirt"
TYPE_HV_POLO = "Hi-Vis Polo"
TYPE_HV_TROUSER = "Hi-Vis Trousers"
TYPE_HV_VEST = "Hi-Vis Waistcoat"
TYPE_HV_JACKET = "Hi-Vis Jacket"
TYPE_HELMET = "Safety Helmet"
TYPE_CAP = "Cap"
TYPE_BEANIE = "Beanie"
TYPE_BACKPACK = "Backpack"
TYPE_TOTE = "Tote"
TYPE_GYMSAC = "Gymsac"
TYPE_BOOK = "Book Bag"
TYPE_PENCIL = "Pencil Case"
TYPE_LUNCH = "Lunch Bag"
TYPE_DRAWSTRING = "Drawstring Bag"
TYPE_BARREL = "Barrel Bag"
TYPE_BAG_ACC = "Bag Accessory"
TYPE_SET = "T-Shirt & Hoodie"
TYPE_STICKER = "Sticker"
TYPE_IRON = "Iron-On Transfer"
TYPE_MUG = "Mug"
TYPE_BADGE = "Badge"
TYPE_CARD = "Card"
TYPE_PHOTO = "Photo Acrylic"
TYPE_MASK = "Face Mask"
TYPE_LOCK = "Baby Drawer Lock"

PRODUCT_TYPES = (
    TYPE_SS_TEE,
    TYPE_LS_TEE,
    TYPE_TANK,
    TYPE_SS_POLO,
    TYPE_LS_POLO,
    TYPE_HOODIE,
    TYPE_ZIP_HOODIE,
    TYPE_SWEAT,
    TYPE_SHIRT,
    TYPE_RUGBY,
    TYPE_JACKET,
    TYPE_FLEECE,
    TYPE_GILET,
    TYPE_CARDIGAN,
    TYPE_TROUSER,
    TYPE_CARGO,
    TYPE_JOGGER,
    TYPE_SHORTS,
    TYPE_BODY,
    TYPE_ROMPER,
    TYPE_BABY_TEE,
    TYPE_TUTU,
    TYPE_TUNIC,
    TYPE_TABARD,
    TYPE_SCRUB,
    TYPE_APRON,
    TYPE_HV_TEE,
    TYPE_HV_POLO,
    TYPE_HV_TROUSER,
    TYPE_HV_VEST,
    TYPE_HV_JACKET,
    TYPE_HELMET,
    TYPE_CAP,
    TYPE_BEANIE,
    TYPE_BACKPACK,
    TYPE_TOTE,
    TYPE_GYMSAC,
    TYPE_BOOK,
    TYPE_PENCIL,
    TYPE_LUNCH,
    TYPE_DRAWSTRING,
    TYPE_BARREL,
    TYPE_BAG_ACC,
    TYPE_SET,
    TYPE_STICKER,
    TYPE_IRON,
    TYPE_MUG,
    TYPE_BADGE,
    TYPE_CARD,
    TYPE_PHOTO,
    TYPE_MASK,
    TYPE_LOCK,
)

# PE Sub-Category — closed, not a 30-chain split.
SUBCATEGORIES = (
    "Short Sleeve T-Shirt",
    "Long Sleeve T-Shirt",
    "Tank Top",
    "Sweatshirts & Hoodies",
    "Polo Shirts",
    "Bags",
    "Caps & Hats",
    "Safety Headwear",
    "Aprons & Tabards",
    "Covers",
)

"""Squeezed warehouse taxonomy for the four Areeb columns (Hashim #038).

Title Case. Product Type has no gender (Department holds that).
Product Style is a named range / simplified product name — never a supplier code.
"""

from __future__ import annotations

DEFAULT_STYLE = "Standard"

# --- Department (Areeb) — gender only ---
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

# Product Style — named ranges / simplified product names. No supplier codes.
PRODUCT_STYLES = (
    DEFAULT_STYLE,
    "Valueweight",
    "Valueweight Baseball",
    "Iconic 150",
    "Original",
    "Heavy Cotton",
    "Softstyle",
    "Ultra Cotton",
    "Heavy Blend",
    "Softstyle Midweight Fleece",
    "Classic",
    "Deluxe",
    "Premium",
    "The UX",
    "Eco",
    "Contrast",
    "Olympic",
    "Active",
    "Heavyweight",
    "Ultra Cool",
    "Super Cool Workwear",
    "Super Pro",
    "Cotton Rich",
    "Ultimate Cotton",
    "Polycotton Workwear",
    "Eco Workwear",
    "Processable",
    "Jersey",
    "Sports",
    "Two Tone",
    "Action",
    "Workwear",
    "Cargo",
    "Cargo Knee Pad",
    "Lightweight",
    "Premium Reversible",
    "Reversible",
    "Premium V-Neck",
    "Classic V-Neck",
    "V-Neck",
    "Ringer",
    "Acid Wash Vintage Rust",
    "Acid Wash Optic Wash",
    "High Visibility",
    "Class 2",
    "Sleeveless Safety",
    "Executive Vest",
    "Hi-Vis Baseball",
    "College",
    "Contrast Cool",
    "Ringspun Blended",
    "Everyday Polo",
    "Softstyle Double Pique",
    "Premium Cotton Polo",
    "Toddler Jersey",
    "Kids Tie Dye",
    "Baby Body Suit",
    "Baby Romper",
    "Baby T-Shirt",
    "Baby Bodysuit",
    "Poplin",
    "Pinpoint Oxford",
    "Quarter Zip",
    "Printable Softshell",
    "Microfleece",
    "Padded",
    "Outdoor",
    "Road Safety",
    "Original Patch",
    "Snowstar Patch",
    "Circular Patch",
    "Rectangular Patch",
    "Pom Pom",
    "Heavyweight Cuffed",
    "6-Panel Low Profile",
    "Classic 5-Panel",
    "Heavyweight 5-Panel",
    "Original 5-Panel Snapback",
    "Snapback Trucker",
    "5-Panel Contrast Snapback",
    "Patch Snapback Trucker",
    "Junior Original 5-Panel Cap",
    "Junior Cotton Cap",
    "Houston 5-Panel Printers Cap",
    "Fairtrade Cotton Junior",
    "Bib With Pocket",
    "Bib Apron",
    "Cotton Adult Apron",
    "Kids Set",
    "A3",
    "A4",
    "A5",
    "A6",
    "Circle",
    "25 mm",
    "Ceramic Mug",
    "Kids T-Shirt",
    "China Bag",
    "Cotton Shopper",
    "Eco Recycled Cotton Tote",
    "Junior Fashion Backpack",
    "Original Fashion Backpack",
    "Maxi Fashion Backpack",
    "Mini Fashion Backpack",
    "Mini Essential Fashion Backpack",
    "Premium Gymsac",
    "Budget Gymsac",
    "Athleisure Gymsac",
    "Cotton Gymsac",
    "Retro Shoulder Bag",
    "Mini Barrel Bag",
    "Packaway Barrel Bag",
    "Junior Dance Bag",
    "Grab Pouch",
    "Ripper Wallet",
    "Belt Bag",
    "Felt Trug",
    "Boutique Circular Key Clip",
    "Boutique Accessory Pouch",
    "Boutique Wristlet Keyring",
    "Lunch Cooler",
    "Water Bottle Holder",
    "Pencil Case",
    "Enhanced-Viz Book Bag",
    "Classic Book Bag",
    "Junior Book Bag",
    "Junior Book Bag With Strap",
    "Teamwear Shoe Bag",
    "Hiking Boot Bag",
    "Boot Bag",
    "Sandwich Lunchbox",
    "Guildford Cotton Tote",
    "Stafford Contrast Drawstring",
    "Cotton Tote",
    "Bag For Life",
    "Bag For Life Short Handles",
    "Cotton Stuff Bag",
    "Cotton Ribbon Cord Bag",
    "Premium Cotton Tote",
    "Organic Premium Maxi Tote",
    "Cotton Cushion Cover",
    "Jute Classic Shopper",
    "Jute Stuff Bag",
    "Printers Jute Shopper",
    "Pocket Jute Gift Bag",
    "Pocket Jute Midi Tote",
    "Cotton Pocket Jute Shopper",
    "Jute Base Canvas Shopper",
    "Jute Base Canvas Tote",
    "Jute Base Canvas Tote XL",
    "Canvas Accessory Case",
    "Canvas Accessory Bag",
    "Gallery Canvas Tote",
    "Fairtrade Cotton Bottle Bag",
    "Nautical Beach Bag",
    "Oversized Canvas Tote",
    "Organic Spring Purse",
    "Organic Accessory Pouch",
    "EarthAware Contrast Shopper",
)

# Supplier code → named style (BTC Description / Absolute / manufacturer site).
STYLE_BY_CODE: dict[str, str] = {
    "5000": "Heavy Cotton",
    "G5000": "Heavy Cotton",
    "2400": "Ultra Cotton",
    "61026": "Valueweight Baseball",
    "61033": "Valueweight",
    "61168": "Ringer",
    "64200": "Softstyle",
    "64200L": "Softstyle",
    "64800": "Softstyle Double Pique",
    "85800L": "Premium Cotton Polo",
    "AA77": "Bib Apron",
    "B10B": "Junior Original 5-Panel Cap",
    "B445": "Original Patch",
    "B610C": "5-Panel Contrast Snapback",
    "B641": "Patch Snapback Trucker",
    "BG10": "Premium Gymsac",
    "BG125": "Original Fashion Backpack",
    "BG125J": "Junior Fashion Backpack",
    "BG125L": "Maxi Fashion Backpack",
    "BG125S": "Mini Fashion Backpack",
    "BG14": "Retro Shoulder Bag",
    "BG140S": "Mini Barrel Bag",
    "BG145": "Junior Dance Bag",
    "BG150": "Packaway Barrel Bag",
    "BG153": "Mini Essential Fashion Backpack",
    "BG38": "Grab Pouch",
    "BG40": "Ripper Wallet",
    "BG42": "Belt Bag",
    "BG5": "Budget Gymsac",
    "BG542": "Athleisure Gymsac",
    "BG728": "Felt Trug",
    "BG745": "Boutique Circular Key Clip",
    "BG750": "Boutique Accessory Pouch",
    "BZ02": "Baby T-Shirt",
    "BZ10": "Baby Bodysuit",
    "C2200": "Ringspun Blended",
    "C2400": "Ringspun Blended",
    "C800T": "Baby Body Suit",
    "C8030T": "Baby Romper",
    "CA3001T": "Toddler Jersey",
    "HVW801": "Executive Vest",
    "JC003": "Contrast Cool",
    "JC03J": "Contrast Cool",
    "JH001": "College",
    "JH01J": "College",
    "M61": "Ceramic Mug",
    "QD435": "Lunch Cooler",
    "QD440": "Water Bottle Holder",
    "QD442": "Pencil Case",
    "QD452": "Enhanced-Viz Book Bag",
    "QD456": "Classic Book Bag",
    "QD457": "Junior Book Bag With Strap",
    "QD51": "Junior Book Bag",
    "QD76": "Teamwear Shoe Bag",
    "QD85": "Hiking Boot Bag",
    "QD86": "Boot Bag",
    "RC05J": "Junior Cotton Cap",
    "RC80X": "Houston 5-Panel Printers Cap",
    "SF500B": "Softstyle Midweight Fleece",
    "SH1808": "Sandwich Lunchbox",
    "SH4112": "Guildford Cotton Tote",
    "SH5891": "Stafford Contrast Drawstring",
    "TD02B": "Kids Tie Dye",
    "TPC001": "Cotton Tote",
    "UCC003": "Everyday Polo",
    "W101": "Bag For Life",
    "W101S": "Bag For Life Short Handles",
    "W110": "Cotton Gymsac",
    "W115": "Cotton Stuff Bag",
    "W121": "Cotton Ribbon Cord Bag",
    "W201": "Premium Cotton Tote",
    "W265": "Organic Premium Maxi Tote",
    "W350": "Cotton Cushion Cover",
    "W364": "Cotton Adult Apron",
    "W407": "Jute Classic Shopper",
    "W415": "Jute Stuff Bag",
    "W422": "Printers Jute Shopper",
    "W425": "Pocket Jute Gift Bag",
    "W426": "Pocket Jute Midi Tote",
    "W427": "Cotton Pocket Jute Shopper",
    "W450": "Jute Base Canvas Shopper",
    "W451": "Jute Base Canvas Tote",
    "W452": "Jute Base Canvas Tote XL",
    "W530": "Canvas Accessory Case",
    "W540": "Canvas Accessory Bag",
    "W544": "Canvas Accessory Bag",
    "W552": "Canvas Accessory Case",
    "W600": "Gallery Canvas Tote",
    "W620": "Fairtrade Cotton Bottle Bag",
    "W680": "Nautical Beach Bag",
    "W696": "Oversized Canvas Tote",
    "W825": "Organic Spring Purse",
    "W830": "Organic Accessory Pouch",
    "W858": "EarthAware Contrast Shopper",
    "6M014V": DEFAULT_STYLE,
}

BAG_TYPE_BY_CODE: dict[str, str] = {
    "BG10": TYPE_GYMSAC,
    "BG125": TYPE_BACKPACK,
    "BG125J": TYPE_BACKPACK,
    "BG125L": TYPE_BACKPACK,
    "BG125S": TYPE_BACKPACK,
    "BG14": TYPE_BAG_ACC,
    "BG140S": TYPE_BARREL,
    "BG145": TYPE_BARREL,
    "BG150": TYPE_BARREL,
    "BG153": TYPE_BACKPACK,
    "BG38": TYPE_BAG_ACC,
    "BG40": TYPE_BAG_ACC,
    "BG42": TYPE_BAG_ACC,
    "BG5": TYPE_GYMSAC,
    "BG542": TYPE_GYMSAC,
    "BG728": TYPE_BAG_ACC,
    "BG745": TYPE_BAG_ACC,
    "BG750": TYPE_BAG_ACC,
    "QD435": TYPE_LUNCH,
    "QD440": TYPE_BAG_ACC,
    "QD442": TYPE_PENCIL,
    "QD452": TYPE_BOOK,
    "QD456": TYPE_BOOK,
    "QD457": TYPE_BOOK,
    "QD51": TYPE_BOOK,
    "QD76": TYPE_BAG_ACC,
    "QD85": TYPE_BAG_ACC,
    "QD86": TYPE_BAG_ACC,
    "SH1808": TYPE_LUNCH,
    "SH4112": TYPE_TOTE,
    "SH5891": TYPE_DRAWSTRING,
    "TPC001": TYPE_TOTE,
    "W101": TYPE_TOTE,
    "W101S": TYPE_TOTE,
    "W110": TYPE_GYMSAC,
    "W115": TYPE_BAG_ACC,
    "W121": TYPE_TOTE,
    "W201": TYPE_TOTE,
    "W265": TYPE_TOTE,
    "W350": TYPE_BAG_ACC,
    "W407": TYPE_TOTE,
    "W415": TYPE_BAG_ACC,
    "W422": TYPE_TOTE,
    "W425": TYPE_BAG_ACC,
    "W426": TYPE_TOTE,
    "W427": TYPE_TOTE,
    "W450": TYPE_TOTE,
    "W451": TYPE_TOTE,
    "W452": TYPE_TOTE,
    "W530": TYPE_BAG_ACC,
    "W540": TYPE_BAG_ACC,
    "W544": TYPE_BAG_ACC,
    "W552": TYPE_BAG_ACC,
    "W600": TYPE_TOTE,
    "W620": TYPE_BAG_ACC,
    "W680": TYPE_TOTE,
    "W696": TYPE_TOTE,
    "W825": TYPE_BAG_ACC,
    "W830": TYPE_BAG_ACC,
    "W858": TYPE_TOTE,
}

HEAD_TYPE_BY_CODE: dict[str, str] = {
    "B10B": TYPE_CAP,
    "B445": TYPE_BEANIE,
    "B610C": TYPE_CAP,
    "B641": TYPE_CAP,
    "RC05J": TYPE_CAP,
    "RC80X": TYPE_CAP,
}

# Longest-first needles found in Gender Apparel after brand/gender strip.
STYLE_PHRASES: tuple[tuple[str, str], ...] = (
    ("softstyle midweight fleece", "Softstyle Midweight Fleece"),
    ("softstyle midw fleece", "Softstyle Midweight Fleece"),
    ("cargo trouser with knee pad pockets", "Cargo Knee Pad"),
    ("with knee pad pockets", "Cargo Knee Pad"),
    ("fairtrade cotton junior", "Fairtrade Cotton Junior"),
    ("eco 100 recycled cotton", "Eco Recycled Cotton Tote"),
    ("acid wash vintage rust", "Acid Wash Vintage Rust"),
    ("acid wash optic wash", "Acid Wash Optic Wash"),
    ("boutique wristlet keyring", "Boutique Wristlet Keyring"),
    ("premium reversible", "Premium Reversible"),
    ("super cool workwear", "Super Cool Workwear"),
    ("polycotton workwear", "Polycotton Workwear"),
    ("pinpoint oxford", "Pinpoint Oxford"),
    ("classic v neck", "Classic V-Neck"),
    ("classic v-neck", "Classic V-Neck"),
    ("premium v-neck", "Premium V-Neck"),
    ("premium v neck", "Premium V-Neck"),
    ("6 panel low profile", "6-Panel Low Profile"),
    ("heavyweight 5 panel", "Heavyweight 5-Panel"),
    ("original snapback 5 panel", "Original 5-Panel Snapback"),
    ("classic 5 panel", "Classic 5-Panel"),
    ("heavweight cuffed", "Heavyweight Cuffed"),
    ("heavyweight cuffed", "Heavyweight Cuffed"),
    ("sleeveless safety", "Sleeveless Safety"),
    ("high visibility", "High Visibility"),
    ("original patch", "Original Patch"),
    ("snowstar patch", "Snowstar Patch"),
    ("circular patch", "Circular Patch"),
    ("rectangular patch", "Rectangular Patch"),
    ("bib apron with pocket", "Bib With Pocket"),
    ("bib with pocket", "Bib With Pocket"),
    ("cotton shopper", "Cotton Shopper"),
    ("china bag", "China Bag"),
    ("china-bag", "China Bag"),
    ("junior fashion backpack", "Junior Fashion Backpack"),
    ("printable softshell", "Printable Softshell"),
    ("printable soft shell", "Printable Softshell"),
    ("quarter zip", "Quarter Zip"),
    ("1/4 zip", "Quarter Zip"),
    ("eco workwear", "Eco Workwear"),
    ("cotton rich", "Cotton Rich"),
    ("ultimate cotton", "Ultimate Cotton"),
    ("ultra cotton", "Ultra Cotton"),
    ("ultra cool", "Ultra Cool"),
    ("heavy cotton", "Heavy Cotton"),
    ("heavy blend", "Heavy Blend"),
    ("iconic 150", "Iconic 150"),
    ("the ux", "The UX"),
    ("super pro", "Super Pro"),
    ("class 2", "Class 2"),
    ("pom pom", "Pom Pom"),
    ("snapback trucker", "Snapback Trucker"),
    ("road safety", "Road Safety"),
    ("kids set", "Kids Set"),
    ("valueweight", "Valueweight"),
    ("softstyle", "Softstyle"),
    ("heavyweight", "Heavyweight"),
    ("lightweight", "Lightweight"),
    ("reversible", "Reversible"),
    ("processable", "Processable"),
    ("two tone", "Two Tone"),
    ("microfleece", "Microfleece"),
    ("micro fleece", "Microfleece"),
    ("bodywarmer", "Padded"),
    ("body warmer", "Padded"),
    ("padded", "Padded"),
    ("outdoor", "Outdoor"),
    ("ringer", "Ringer"),
    ("classic", "Classic"),
    ("deluxe", "Deluxe"),
    ("premium", "Premium"),
    ("olympic", "Olympic"),
    ("active", "Active"),
    ("contrast", "Contrast"),
    ("jersey", "Jersey"),
    ("sports", "Sports"),
    ("original", "Original"),
    ("workwear", "Workwear"),
    ("action", "Action"),
    ("cargo", "Cargo"),
    ("poplin", "Poplin"),
    ("eco", "Eco"),
    ("v neck", "V-Neck"),
    ("v-neck", "V-Neck"),
)

# Styles that duplicate the product type — collapse to Standard.
TYPE_DUPLICATE_STYLES = frozenset(
    {
        "T-Shirt",
        "T Shirt",
        "Hoodie",
        "Sweatshirt",
        "Polo",
        "Polo Shirt",
        "Shirt",
        "Trouser",
        "Trousers",
        "Jacket",
        "Fleece",
        "Gilet",
        "Cap",
        "Beanie",
        "Mug",
        "Sticker",
        "Apron",
        "Tunic",
        "Scrub",
        "Tabard",
        "Tutu",
        "Cardigan",
        "Joggers",
        "Shorts",
        "Face Mask",
        "Badge",
        "Card",
        "Photo Acrylic",
        "Iron-On",
        "Bag",
        "Babywear",
        "Vest",
        "Tank",
        "Helmet",
        "Hi-Vis",
        "Hi-Viz",
        "Hi-Viz Polo",
        "Hi-Viz T-Shirt",
        "Hi-Viz Trouser",
        "Hi-Viz Waistcoat",
        "Hi-Viz Jacket",
        "Long",
        "Short",
        "Regular",
        "Long Sleeve",
        "Long Sleeve Polo",
        "Softstyle Tank",
    }
)

# Old harvest / fill spellings → canonical (only where casefold is not enough).
ALIASES: dict[str, dict[str, str]] = {
    "category": {
        "SWEATSHIRTS AND HOODIES": CAT_SWEAT,
        "Sweatshirts And Hoodies": CAT_SWEAT,
        "Rugby Shirts": CAT_SHIRT,
        "Joggers": CAT_TROUSER,
        "Tutus": CAT_BABY,
        "Masks": CAT_ACC,
        "Badges": CAT_ACC,
        "Cards": CAT_ACC,
        "Photo Acrylic": CAT_ACC,
        "CAPS & HATS": CAT_HEAD,
        "OUTERWEAR": CAT_JACKET,
        "Hospitallity": CAT_HOSP,
        "Shirts & Blouses": CAT_SHIRT,
        "TROUSERS & JOGPANTS": CAT_TROUSER,
        "T-SHIRTS": CAT_TEE,
        "POLO SHIRTS": CAT_POLO,
        "HEADWEAR": CAT_HEAD,
    },
    "product_type": {
        "MENS SHORT SLEEVE T-SHIRT": TYPE_SS_TEE,
        "Mens Short Sleeve T-Shirt": TYPE_SS_TEE,
        "Ladies Short Sleeve T-Shirts": TYPE_SS_TEE,
        "Childrens T-Shirt": TYPE_SS_TEE,
        "Unisex T-Shirt": TYPE_SS_TEE,
        "UNISEX T-SHIRT": TYPE_SS_TEE,
        "Mens Long Sleeve T-Shirt": TYPE_LS_TEE,
        "MENS LONG SLEEVE T-SHIRTS": TYPE_LS_TEE,
        "Ladies Long Sleeve T-Shirt": TYPE_LS_TEE,
        "LADIES LONG SLEEVE T-SHIRTS": TYPE_LS_TEE,
        "Childrens Long Sleeve T-Shirt": TYPE_LS_TEE,
        "Athletic Vest": TYPE_TANK,
        "Mens Tank Tops, Vest Etc": TYPE_TANK,
        "Mens Tank Tops, Vests Etc": TYPE_TANK,
        "Ladies Vests, Camisoles, Etc.": TYPE_TANK,
        "Childrens Vest": TYPE_TANK,
        "MENS SHORT SLEEVE POLO SHIRTS": TYPE_SS_POLO,
        "Ladies Short Sleeve Polo Shirts": TYPE_SS_POLO,
        "Childrens Polo Shirt": TYPE_SS_POLO,
        "Childrens Polo Shirts": TYPE_SS_POLO,
        "Unisex Polo Shirt": TYPE_SS_POLO,
        "Unisex Polo": TYPE_SS_POLO,
        "Mens Long Sleeve Polo Shirt": TYPE_LS_POLO,
        "Mens Long Sleeve Polo Shirts": TYPE_LS_POLO,
        "Ladies Long Sleeve Polo Shirt": TYPE_LS_POLO,
        "Ladies Long Sleeve Polo Shirts": TYPE_LS_POLO,
        "Mens Sweatshirts & Hoodies": TYPE_HOODIE,
        "Ladies Sweatshirts And Hoodies": TYPE_HOODIE,
        "Childrens Sweatshirts And Hoodies": TYPE_HOODIE,
        "Unisex Sweatshirts & Hoodies": TYPE_HOODIE,
        "UNISEX SWEATSHIRTS & HOODIES": TYPE_HOODIE,
        "Unisex Sweats And Hoodies": TYPE_HOODIE,
        "Mens Woven Shirt": TYPE_SHIRT,
        "Ladies Woven Shirt": TYPE_SHIRT,
        "Childrens Woven Shirt": TYPE_SHIRT,
        "Rugby Shirt": TYPE_RUGBY,
        "Mens Jacket": TYPE_JACKET,
        "Ladies Jacket": TYPE_JACKET,
        "Childrens Jacket": TYPE_JACKET,
        "Childrens jackets": TYPE_JACKET,
        "MENS OUTER JACKETS": TYPE_JACKET,
        "Mens Fleece": TYPE_FLEECE,
        "Ladies Fleece": TYPE_FLEECE,
        "Childrens Fleece": TYPE_FLEECE,
        "Childrens Fleeces": TYPE_FLEECE,
        "Mens Trousers": TYPE_TROUSER,
        "Ladies Trousers": TYPE_TROUSER,
        "Childrens Trousers": TYPE_TROUSER,
        "Mens Trousers And Jogpants": TYPE_TROUSER,
        "Ladies Trousers And Jog Pants": TYPE_TROUSER,
        "Jog Bottoms": TYPE_JOGGER,
        "Hi-Viz T-Shirt": TYPE_HV_TEE,
        "Hi-Viz Polo Shirt": TYPE_HV_POLO,
        "Hi-Vis Trouser": TYPE_HV_TROUSER,
        "Hi-Viz Trouser": TYPE_HV_TROUSER,
        "Hi-Vis Waistcoat": TYPE_HV_VEST,
        "Hi-Vis Jacket": TYPE_HV_JACKET,
        "Safety Helmet": TYPE_HELMET,
        "Bags, Backpacks Etc": TYPE_BACKPACK,
        "T-Shirt and Hoodie": TYPE_SET,
        "Baby And Toddlerwear": TYPE_BODY,
        "Ladies Tunic": TYPE_TUNIC,
        "Mens Tunic": TYPE_TUNIC,
        "Iron-On Transfer": TYPE_IRON,
        "Baby Drawer Lock": TYPE_LOCK,
        "Photo Acrylic": TYPE_PHOTO,
    },
    "product_style": {
        "China-Bag": "China Bag",
        "Heavweight Cuffed": "Heavyweight Cuffed",
        "Softstyle Tank": "Softstyle",
        "Classic 5": "Classic 5-Panel",
        "Heavyweight 5": "Heavyweight 5-Panel",
        "Original 5": "Original 5-Panel Snapback",
        "6 Panel Low Profile": "6-Panel Low Profile",
        "25mm": "25 mm",
        "Premium V-neck": "Premium V-Neck",
        "Junior Fashion": "Junior Fashion Backpack",
        "Eco 100 Recycled Cotton": "Eco Recycled Cotton Tote",
        "T-Shirt": DEFAULT_STYLE,
        "Hoodie": DEFAULT_STYLE,
        "Sweatshirt": DEFAULT_STYLE,
        "Polo": DEFAULT_STYLE,
        "Shirt": DEFAULT_STYLE,
        "Mug": DEFAULT_STYLE,
        "Sticker": DEFAULT_STYLE,
        "Face Mask": DEFAULT_STYLE,
        "Cap": DEFAULT_STYLE,
        "Jacket": DEFAULT_STYLE,
        "Fleece": DEFAULT_STYLE,
        "Gilet": DEFAULT_STYLE,
        "Trouser": DEFAULT_STYLE,
        "Shorts": DEFAULT_STYLE,
        "Joggers": DEFAULT_STYLE,
        "Tunic": DEFAULT_STYLE,
        "Scrub": DEFAULT_STYLE,
        "Tutu": DEFAULT_STYLE,
        "Cardigan": DEFAULT_STYLE,
        "Long": "Cargo",
        "Short": "Cargo",
        "Regular": "Cargo",
        "With Knee Pad Pockets Long": "Cargo Knee Pad",
        "With Knee Pad Pockets Regular": "Cargo Knee Pad",
        "Hi-Viz Polo": "High Visibility",
        "Hi-Viz T-Shirt": "High Visibility",
        "Hi-Viz Trouser": "High Visibility",
        "Hi-Viz Waistcoat": "High Visibility",
        "Safety": "High Visibility",
        "Baseball": "Hi-Vis Baseball",
        "Heavy": "Heavy Cotton",
        "K-T": "Kids T-Shirt",
        "Iron-On": DEFAULT_STYLE,
        "Bag": DEFAULT_STYLE,
        "Apron": "Bib Apron",
        "Beanie": DEFAULT_STYLE,
        "Helmet": "Hi-Vis Baseball",
        "Badge": DEFAULT_STYLE,
        "Card": "A5",
        "Photo Acrylic": DEFAULT_STYLE,
        "Baby Drawer Lock": DEFAULT_STYLE,
        "Babywear": "Baby T-Shirt",
        "Tank": "Softstyle",
        "Vest": DEFAULT_STYLE,
        "Rugby Shirt": "Classic",
        "Tabard": "Premium",
        "Hi-Vis": "Class 2",
        "Hi-Viz Jacket": "High Visibility",
        "Long Sleeve": DEFAULT_STYLE,
        "Long Sleeve Polo": DEFAULT_STYLE,
    },
    "subcategory": {
        "Mens Short Sleeve T-Shirt": "Short Sleeve T-Shirt",
        "Ladies Short Sleeve T-Shirts": "Short Sleeve T-Shirt",
        "Childrens T-Shirt": "Short Sleeve T-Shirt",
        "Mens Long Sleeve T-Shirts": "Long Sleeve T-Shirt",
        "Mens Tank Tops, Vest Etc": "Tank Top",
        "Mens Tank Tops, Vests Etc": "Tank Top",
        "Ladies Vests, Camisoles, Etc.": "Tank Top",
        "Mens Sweatshirts & Hoodies": "Sweatshirts & Hoodies",
        "Childrens Sweatshirts And Hoodies": "Sweatshirts & Hoodies",
        "Mens Short Sleeve Polo Shirts": "Polo Shirts",
        "Bags, Backpacks Etc": "Bags",
        "Caps & Hats Etc": "Caps & Hats",
        "Aprons And Tabards": "Aprons & Tabards",
    },
    "department": {},
}

# Add every supplier code as a style alias so a leftover code cell snaps to the name.
for _code, _name in STYLE_BY_CODE.items():
    ALIASES["product_style"].setdefault(_code, _name)
    ALIASES["product_style"].setdefault(_code.lower(), _name)


def style_from_code(token: object) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    return STYLE_BY_CODE.get(raw.upper(), "")


def bag_type_from_code(token: object) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    return BAG_TYPE_BY_CODE.get(raw.upper(), "")


def head_type_from_code(token: object) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    return HEAD_TYPE_BY_CODE.get(raw.upper(), "")


def collapse_style(style: str) -> str:
    s = (style or "").strip()
    if not s:
        return ""
    if s.casefold() in {x.casefold() for x in TYPE_DUPLICATE_STYLES}:
        return DEFAULT_STYLE
    return s


def csv_rows() -> list[tuple[str, str, str, str]]:
    """dimension, value, maps_to, source — canonical first, then aliases."""
    blocks: list[tuple[str, tuple[str, ...]]] = [
        ("category", CATEGORIES),
        ("subcategory", SUBCATEGORIES),
        ("product_type", PRODUCT_TYPES),
        ("product_style", PRODUCT_STYLES),
        ("department", DEPARTMENTS),
    ]
    rows: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for dim, values in blocks:
        folded = [s.casefold() for s in values]
        if len(folded) != len(set(folded)):
            raise ValueError(f"duplicate {dim} values")
        for value in values:
            key = (dim, value.casefold())
            if key in seen:
                continue
            seen.add(key)
            rows.append((dim, value, "", "warehouse"))
        for alias, canonical in sorted(ALIASES.get(dim, {}).items(), key=lambda kv: kv[0].casefold()):
            if alias.casefold() == canonical.casefold():
                continue
            if canonical not in values and canonical.casefold() not in folded:
                raise ValueError(f"{dim} alias {alias!r} maps to unknown {canonical!r}")
            key = (dim, alias.casefold())
            if key in seen:
                continue
            seen.add(key)
            rows.append((dim, alias, canonical, "alias"))
    return rows

"""Lookup maps and shirt/position regexes for fill_from_seeds."""
from __future__ import annotations

import re

AGE_TO_PRINT = {
    "1-2 Years": "1-2 Years",
    "1-2Y": "1-2 Years",
    "2-3 Years": "2-3 Years",
    "2-3Y": "2-3 Years",
    "3-4 Years": "3-4 Years/YXS",
    "3-4Y": "3-4 Years/YXS",
    "3-4 Years/YXS": "3-4 Years/YXS",
    "3-4Y/YXS": "3-4 Years/YXS",
    "YXS": "3-4 Years/YXS",
    "5-6 Years": "5-6 Years/YS",
    "5-6Y": "5-6 Years/YS",
    "5-6 Years/YS": "5-6 Years/YS",
    "5-6Y/YS": "5-6 Years/YS",
    "YS": "5-6 Years/YS",
    "7-8 Years": "7-8 Years/YM",
    "7-8Y": "7-8 Years/YM",
    "7-8 Years/YM": "7-8 Years/YM",
    "7-8Y/YM": "7-8 Years/YM",
    "YM": "7-8 Years/YM",
    "9-11 Years": "9-11 Years/YL",
    "9-11Y": "9-11 Years/YL",
    "9-11 Years/YL": "9-11 Years/YL",
    "9-11Y/YL": "9-11 Years/YL",
    "YL": "9-11 Years/YL",
    "12-13 Years": "12-13 Years/YXL",
    "12-13Y": "12-13 Years/YXL",
    "12-13 Years/YXL": "12-13 Years/YXL",
    "12-13Y/YXL": "12-13 Years/YXL",
    "YXL": "12-13 Years/YXL",
    # Print Sizes has no 14-15 band; warehouse uses Small A4 (237×336), same as existing M25 14-15Y.
    "14-15 Years": "Small",
    "14-15Y": "Small",
    "12-14 Years": "Small",
}

AGE_TO_SR = {
    "1-2 Years": "1-2Y",
    "1-2Y": "1-2Y",
    "2-3 Years": "2-3Y",
    "2-3Y": "2-3Y",
    "3-4 Years": "3-4Y",
    "3-4Y": "3-4Y",
    "5-6 Years": "5-6Y",
    "5-6Y": "5-6Y",
    "7-8 Years": "7-8Y",
    "7-8Y": "7-8Y",
    "9-11 Years": "9-11Y",
    "9-11Y": "9-11Y",
    "12-13 Years": "12-13Y",
    "12-13Y": "12-13Y",
    "12-14 Years": "14-15Y",
    "14-15 Years": "14-15Y",
    "14-15Y": "14-15Y",
}

LETTER_TO_SR = {
    "Extra Small": "XS",
    "XS": "XS",
    "Small": "Small",
    "S": "Small",
    "Medium": "Medium",
    "M": "Medium",
    "Large": "Large",
    "L": "Large",
    "Extra Large": "XL",
    "XL": "XL",
    "2XL": "2XL",
    "XXL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

LETTER_TO_MEN_PRINT = {
    "Extra Small": "Small",
    "XS": "Small",
    "Small": "Small",
    "S": "Small",
    "Medium": "Medium",
    "M": "Medium",
    "Large": "Large",
    "L": "Large",
    "Extra Large": "XL",
    "XL": "XL",
    "2XL": "2XL",
    "XXL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

RE_SHIRT_GA = re.compile(
    r"t-?shirt|\btee\b|\bpolo\b|hoodie|sweat|\btank\b|"
    r"original t\b|iconic \d+ t\b|valueweight t\b",
    re.I,
)
RE_NOT_SHIRT_GA = re.compile(
    r"bag|tote|apron|beanie|\bhat\b|\bcap\b|iron.?on|"
    r"romper|bodysuit|waistcoat|sticker|\bmug\b|\bmask\b",
    re.I,
)
RE_SHIRT_SKU = re.compile(r"(^|-)[MWK]-T(-|$)", re.I)

PE_AGE = {
    "1-2": "1-2Y",
    "2-3": "2-3Y",
    "3-4": "3-4Y",
    "5-6": "5-6Y",
    "7-8": "7-8Y",
    "9-11": "9-11Y",
    "12-13": "12-13Y",
    "14-15": "14-15Y",
}

SUFFIX_TO_NAME = {
    "P": "Front Left Pocket",
    "F": "Front Center",
    "B": "Back Center",
    "S": "Sleeve",
    "S-1": "Sleeve",
}

KNOWN_HUMAN = {
    "front center",
    "back center",
    "front left pocket",
    "front right pocket",
    "front bottom left corner",
    "front bottom right corner",
    "right sleeve",
    "sleeve",
    "inside",
}

"""CL warehouse classify: pattern engine + cl_standard entry point."""
from __future__ import annotations

from typing import Any, Mapping

from shared.areeb_taxonomy.cl_garment import _garment_kind
from shared.areeb_taxonomy.cl_rules import CL_STANDARD_RULES, CL_STANDARD_RULES_FOLD
from shared.areeb_taxonomy.cl_style import _style_from_ga
from shared.areeb_taxonomy.cl_type import _department_for, _product_type
from shared.areeb_taxonomy.values import AreebValues, _norm_ga, _values_from_tuple
from shared.taxonomy_picklist import snap_warehouse


def _classify_ga_pattern(ga: str) -> AreebValues:
    hit = _garment_kind(ga)
    if not hit:
        return AreebValues()
    category, kind = hit
    dept = _department_for(ga, category)
    return _values_from_tuple(
        (category, _product_type(category, kind, ga), _style_from_ga(ga, kind), dept)
    )


def _snap_cl_areeb(values: AreebValues) -> AreebValues:
    """Hashim #038: warehouse fill picks from the closed list; do not invent."""
    if not values.any_filled():
        return values
    category, product_type, product_style, department = snap_warehouse(
        category=values.category,
        product_type=values.product_type,
        product_style=values.product_style,
        department=values.department,
    )
    return AreebValues(
        category=category,
        product_type=product_type,
        product_style=product_style,
        department=department or values.department,
        source=values.source,
    )


def cl_standard(row: Mapping[str, Any]) -> AreebValues:
    """Warehouse Areeb 4-tuple from Gender Apparel. Department is gender only."""
    ga = _norm_ga(row.get("Gender Apparel"))
    if not ga:
        return AreebValues()
    exact = CL_STANDARD_RULES.get(ga) or CL_STANDARD_RULES_FOLD.get(ga.casefold())
    if exact:
        return _snap_cl_areeb(_values_from_tuple(exact))
    return _snap_cl_areeb(_classify_ga_pattern(ga))


leftover_cl = cl_standard
classify_cl = cl_standard

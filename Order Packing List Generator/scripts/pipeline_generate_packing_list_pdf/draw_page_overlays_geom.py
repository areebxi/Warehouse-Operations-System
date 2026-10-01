"""Logo overlay geometry (slot rects on the apparel mockup)."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def overlay_slot_geometry(
    ax: float, ay: float, aw: float, ah: float
) -> Dict[str, Tuple[float, float, float, float]]:
    front_chest_scale = 2.5
    front_w = aw / front_chest_scale
    front_h = ah / front_chest_scale
    front_lx = ax + aw * 0.3
    front_ly = ay + ah * 0.4

    pocket_scale = 6.0
    pocket_w = aw / pocket_scale
    pocket_h = ah / pocket_scale
    pocket_lx = ax + aw * 0.555
    pocket_ly = ay + ah * 0.675

    left_forearm_scale = 6.0
    left_forearm_w = aw / left_forearm_scale
    left_forearm_h = ah / left_forearm_scale
    left_forearm_lx = ax + aw * 0.735
    left_forearm_ly = ay + ah * 0.185

    right_forearm_scale = left_forearm_scale
    right_forearm_w = aw / right_forearm_scale
    right_forearm_h = ah / right_forearm_scale
    right_forearm_lx = ax + aw * 0.08
    right_forearm_ly = left_forearm_ly

    bottom_left_scale = 2.5
    bottom_left_w = aw / bottom_left_scale
    bottom_left_h = ah / bottom_left_scale
    bottom_left_lx = ax + aw * 0.155
    bottom_left_ly = ay + ah * 0.125

    bottom_right_scale = bottom_left_scale
    bottom_right_w = aw / bottom_right_scale
    bottom_right_h = ah / bottom_right_scale
    bottom_right_lx = ax + aw * 0.415
    bottom_right_ly = bottom_left_ly

    return {
        "front_chest": (front_lx, front_ly, front_w, front_h),
        "pocket": (pocket_lx, pocket_ly, pocket_w, pocket_h),
        "left_front_full_forearm": (
            left_forearm_lx,
            left_forearm_ly,
            left_forearm_w,
            left_forearm_h,
        ),
        "right_front_full_forearm": (
            right_forearm_lx,
            right_forearm_ly,
            right_forearm_w,
            right_forearm_h,
        ),
        "front_bottom_left": (bottom_left_lx, bottom_left_ly, bottom_left_w, bottom_left_h),
        "front_bottom_right": (
            bottom_right_lx,
            bottom_right_ly,
            bottom_right_w,
            bottom_right_h,
        ),
    }


def geometry_keys_from_draw_tokens(
    draw_tokens: List[str], *, normalize_lower
) -> List[Optional[str]]:
    geometry_keys: List[Optional[str]] = []
    for dt in draw_tokens:
        key = normalize_lower(dt)
        if not key:
            geometry_keys.append(None)
        elif key in ("front", "front center"):
            geometry_keys.append("front_chest")
        elif key == "pocket":
            geometry_keys.append("pocket")
        elif key == "front left full forearm":
            geometry_keys.append("left_front_full_forearm")
        elif key == "front right full forearm":
            geometry_keys.append("right_front_full_forearm")
        elif key == "front bottom left corner":
            geometry_keys.append("front_bottom_left")
        elif key == "front bottom right corner":
            geometry_keys.append("front_bottom_right")
        else:
            geometry_keys.append(None)
    return geometry_keys

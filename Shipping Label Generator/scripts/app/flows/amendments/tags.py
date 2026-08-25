from __future__ import annotations

from dataclasses import dataclass, field


AMENDMENTS_TAG_NAME = "Amendments"
AMENDMENTS_SKIP_REASON = (
    "Order has Amendments tag; label not printed until amendments are complete."
)


@dataclass(frozen=True)
class OrderTagInfo:
    order_number: str
    order_id: int | None
    tag_ids: list[int] = field(default_factory=list)
    tag_names: list[str] = field(default_factory=list)
    order_status: str = ""
    customer_name: str = ""

    @property
    def tag_count(self) -> int:
        return len(self.tag_names) if self.tag_names else len(self.tag_ids)

    @property
    def has_amendments(self) -> bool:
        return has_amendments_tag(self.tag_names)


def _norm_tag(name: str) -> str:
    return str(name or "").strip().casefold()


def has_amendments_tag(tag_names: list[str] | tuple[str, ...] | None, *, tag_name: str = AMENDMENTS_TAG_NAME) -> bool:
    """True if any tag name matches Amendments (case-insensitive, trimmed)."""
    target = _norm_tag(tag_name)
    if not target:
        return False
    for n in tag_names or []:
        if _norm_tag(n) == target:
            return True
    return False


def should_skip_label_for_amendments(
    tag_names: list[str] | tuple[str, ...] | None,
    *,
    tag_name: str = AMENDMENTS_TAG_NAME,
) -> bool:
    """Whether Print should refuse to generate a label for this order."""
    return has_amendments_tag(tag_names, tag_name=tag_name)


def amendments_skip_reason(*, tag_name: str = AMENDMENTS_TAG_NAME) -> str:
    """Reason text for the missed/error page when Amendments blocks printing."""
    if _norm_tag(tag_name) == _norm_tag(AMENDMENTS_TAG_NAME):
        return AMENDMENTS_SKIP_REASON
    clean = str(tag_name or "").strip() or AMENDMENTS_TAG_NAME
    return f"Order has {clean} tag; label not printed until amendments are complete."

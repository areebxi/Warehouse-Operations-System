"""Report PDF text helpers (truncate / escape)."""

from __future__ import annotations

from xml.sax.saxutils import escape


def _truncate_text(s: str, *, max_chars: int) -> str:
    t = str(s or "")
    if max_chars <= 0:
        return ""
    if len(t) <= max_chars:
        return t
    suffix = "\n\n...(truncated)"
    if len(suffix) >= max_chars:
        return t[:max_chars]
    keep = max_chars - len(suffix)
    return t[:keep] + suffix


def _error_reason_paragraph_text(reason: str, *, max_chars: int = 1800) -> str:
    """
    ReportLab Paragraphs are XML-ish. Escape + convert newlines to <br/>.
    Also hard-truncate to avoid pathological layouts when ShipStation returns huge JSON bodies.
    """
    t = _truncate_text(reason, max_chars=max_chars)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = escape(t, {"\n": "<br/>"})
    return t.replace("\n", "<br/>")


def _plain_cell_text(s: str, *, max_chars: int) -> str:
    # Table cells use plain strings (not Paragraph). Keep them bounded too.
    return _truncate_text(s, max_chars=max_chars)


def _summary_process_font_size(process_number: str) -> int:
    """Scale the large process number so long values stay inside the summary table."""
    n = len(str(process_number).strip())
    if n <= 4:
        return 144
    if n <= 6:
        return 96
    if n <= 8:
        return 72
    if n <= 12:
        return 48
    return 36

import re

NUMBER_RE = re.compile(r"^\d+([.,]\d+)?$")


def parse_qty(text: str) -> float:
    """
    Parse a positive quantity number.
    Accepts comma or dot as decimal separator.
    Raises ValueError if invalid or <= 0.
    """
    raw = (text or "").strip().replace(",", ".")
    if not NUMBER_RE.match(raw):
        raise ValueError("Invalid number format")
    qty = float(raw)
    if qty < 0:
        raise ValueError("Quantity must be => 0")
    return qty


def parse_limit(text: str) -> float | None:
    """
    Parse limit quantity.
    Returns None if user wants to remove the limit ("-", "0", empty).
    Raises ValueError for invalid input.
    """
    raw = (text or "").strip()
    if raw in ("", "-", "0", "0.0", "0.00"):
        return None

    if not NUMBER_RE.match(raw):
        raise ValueError("Invalid number format")

    val = float(raw.replace(",", "."))
    if val <= 0:
        return None
    return val

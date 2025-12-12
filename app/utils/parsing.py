def parse_qty(text: str) -> float:
    """
    Parse a positive quantity number.
    Accepts comma or dot as decimal separator.
    """
    raw = (text or "").strip().replace(",", ".")
    qty = float(raw)
    if qty <= 0:
        raise ValueError("qty must be > 0")
    return qty


def parse_limit(text: str):
    """
    Parse limit quantity.
    Returns None if user wants to remove the limit ("-", "0", empty).
    """
    raw = (text or "").strip().replace(",", ".")
    if raw in ("", "-", "0", "0.0", "0.00"):
        return None
    val = float(raw)
    if val <= 0:
        return None
    return val

def fmt_amount(n) -> str:
    n = float(n)
    if n.is_integer():
        return f"${int(n):,}"
    return f"${n:,.2f}"

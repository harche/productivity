#!/usr/bin/env python3
"""
Display IBKR account summary with key financial metrics.

Usage:
    python3 account_summary.py
"""

from __future__ import annotations

from ibkr_client import initialize_session, get_account_id, get_account_summary


# Metrics to display: (display label, summary key, formatting style)
METRICS: list[tuple[str, str, str]] = [
    ("Net Liquidation Value",  "netliquidation",       "currency"),
    ("Equity with Loan",       "equitywithloanvalue",   "currency"),
    ("Available Funds",        "availablefunds",        "currency"),
    ("Buying Power",           "buyingpower",           "currency"),
    ("Maintenance Margin",     "maintmarginreq",        "currency"),
    ("Initial Margin",         "initmarginreq",         "currency"),
    ("Cushion",                "cushion",               "percent"),
    ("Day Trades Remaining",   "daytradesremaining",    "integer"),
]


def extract_value(summary: dict, key: str) -> float | str | None:
    """Extract a numeric value from a summary field. Handles both flat and nested formats."""
    entry: dict | float | str | None = summary.get(key)
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry.get("amount", entry.get("value"))
    return entry


def format_value(raw: float | str | None, style: str) -> str:
    """Format a raw value according to the given style."""
    if raw is None:
        return "N/A"
    try:
        numeric: float = float(raw)
    except (ValueError, TypeError):
        return str(raw)

    if style == "currency":
        return f"${numeric:>15,.2f}"
    elif style == "percent":
        return f"{numeric * 100:>15.2f}%"
    elif style == "integer":
        return f"{int(numeric):>15,}"
    else:
        return f"{numeric:>15}"


def display_summary(summary: dict) -> None:
    """Format and print the account summary as a clean table."""
    label_width: int = max(len(label) for label, _, _ in METRICS)
    separator: str = "-" * (label_width + 20)

    print()
    print(separator)
    print(f"  {'ACCOUNT SUMMARY':^{label_width + 16}}")
    print(separator)

    for label, key, style in METRICS:
        raw_value: float | str | None = extract_value(summary, key)
        formatted: str = format_value(raw_value, style)
        print(f"  {label:<{label_width}}  {formatted}")

    print(separator)

    # Show currency if available
    currency: str | None = None
    nlv_entry: dict | None = summary.get("netliquidation")
    if isinstance(nlv_entry, dict):
        currency = nlv_entry.get("currency", nlv_entry.get("cur"))
    if currency:
        print(f"  {'Currency:':<{label_width}}  {currency:>15}")
        print(separator)

    print()


def main() -> None:
    initialize_session()
    account_id: str = get_account_id()

    print(f"\nFetching summary for account {account_id}...")
    summary: dict = get_account_summary(account_id)
    display_summary(summary)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
IBKR Account Summary.

Usage:
    python account_summary.py
    python account_summary.py --port 4001    # live trading
"""

from __future__ import annotations

import argparse

from ib_client import connect


def main() -> None:
    parser = argparse.ArgumentParser(description="IBKR account summary.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    args = parser.parse_args()

    ib = connect(args.host, args.port)

    print(f"\n{'=' * 60}")
    print(f"  ACCOUNT SUMMARY")
    print(f"{'=' * 60}")

    key_tags = [
        "NetLiquidation", "TotalCashValue", "GrossPositionValue",
        "BuyingPower", "AvailableFunds", "ExcessLiquidity",
        "InitMarginReq", "MaintMarginReq",
        "FullInitMarginReq", "FullMaintMarginReq",
    ]

    values = ib.accountValues()
    base_currency = None
    for v in values:
        if v.tag == "NetLiquidation" and v.value:
            base_currency = v.currency
            break

    shown = set()
    for tag in key_tags:
        for v in values:
            if v.tag == tag and v.currency == base_currency and tag not in shown:
                try:
                    val = float(v.value)
                    print(f"  {tag:<24} ${val:>14,.2f}")
                except ValueError:
                    print(f"  {tag:<24} {v.value}")
                shown.add(tag)

    print(f"{'=' * 60}")
    ib.disconnect()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Iron Butterfly/Condor Strategy Builder for SPX via IBKR Client Portal Gateway API.

Selects ATM strikes, calculates wing widths for max_loss = 2x max_profit,
and outputs an order JSON file that can be submitted via submit_order.py.

Requires: pip install requests

Usage:
    python iron_butterfly.py today
    python iron_butterfly.py tomorrow --quantity 2
    python iron_butterfly.py 2026-03-10 --output my_order.json
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

import warnings
warnings.filterwarnings("ignore")

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    print("Installing requests ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests"])
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://localhost:5000/v1/api"
SPX_CONID = 416904
STRIKE_INCREMENT = 5
REQUEST_DELAY = 0.15
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_get(path, params=None, retries=2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.get(url, params=params, verify=False, timeout=15)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue
        resp.raise_for_status()
        return resp.json()


def api_post(path, json_body=None, retries=2):
    url = f"{BASE_URL}{path}"
    for attempt in range(retries + 1):
        resp = requests.post(url, json=json_body, verify=False, timeout=15)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(1)
            continue
        resp.raise_for_status()
        return resp.json()


def round_to_strike(value):
    return int(round(value / STRIKE_INCREMENT) * STRIKE_INCREMENT)


def parse_expiry(expiry_arg):
    today = datetime.now().date()
    if expiry_arg.lower() == "today":
        return today
    elif expiry_arg.lower() == "tomorrow":
        return today + timedelta(days=1)
    else:
        return datetime.strptime(expiry_arg, "%Y-%m-%d").date()


def month_code(dt):
    return dt.strftime("%b%y").upper()


def maturity_str(dt):
    return dt.strftime("%Y%m%d")


def parse_price(field_val):
    if field_val is None:
        return None
    if isinstance(field_val, (int, float)):
        return float(field_val)
    if isinstance(field_val, str):
        cleaned = field_val.lstrip("CHch")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# API interactions
# ---------------------------------------------------------------------------

def initialize_session():
    print("[1/9] Initializing session ...")
    accounts = api_get("/iserver/accounts")
    acct_list = accounts.get("accounts", [])
    print(f"       Accounts: {acct_list}")
    time.sleep(REQUEST_DELAY)

    status = api_get("/iserver/auth/status")
    print(f"       Auth: authenticated={status.get('authenticated')}, connected={status.get('connected')}")
    if not status.get("authenticated"):
        sys.exit("ERROR: Session is not authenticated. Ensure the Client Portal Gateway is running and logged in.")
    time.sleep(REQUEST_DELAY)


def get_account_id():
    accounts = api_get("/portfolio/accounts")
    account_id = accounts[0]["accountId"]
    print(f"       Account ID: {account_id}")
    time.sleep(REQUEST_DELAY)
    return account_id


def get_spx_price():
    print("[2/9] Fetching SPX price ...")
    data = api_get("/iserver/marketdata/history", params={
        "conid": SPX_CONID, "period": "1d", "bar": "1h",
    })
    bars = data.get("data", [])
    if not bars:
        raise RuntimeError("No historical data returned for SPX")
    price = bars[-1]["c"]
    print(f"       SPX: {price}")
    time.sleep(REQUEST_DELAY)
    return price


def get_option_contract(strike, right, expiry_date):
    month = month_code(expiry_date)
    target = maturity_str(expiry_date)
    contracts = api_get("/iserver/secdef/info", params={
        "conid": SPX_CONID, "sectype": "OPT", "month": month,
        "exchange": "SMART", "strike": str(strike), "right": right,
    })
    time.sleep(REQUEST_DELAY)

    matched = [c for c in contracts if c.get("maturityDate") == target]
    if not matched:
        raise RuntimeError(f"No contract for strike={strike} right={right} maturity={target}")

    spxw = [c for c in matched if c.get("tradingClass") == "SPXW"]
    return spxw[0] if spxw else matched[0]


def get_option_prices(conids):
    """Get bid/ask/last for multiple conids in one batch (prime + read)."""
    conid_str = ",".join(str(c) for c in conids)
    params = {"conids": conid_str, "fields": "31,84,86"}

    api_get("/iserver/marketdata/snapshot", params=params)
    time.sleep(2.5)
    data = api_get("/iserver/marketdata/snapshot", params=params)
    time.sleep(REQUEST_DELAY)

    results = {}
    for snap in (data if isinstance(data, list) else [data]):
        cid = snap.get("conid")
        results[cid] = {
            "conid": cid,
            "last": parse_price(snap.get("31")),
            "bid": parse_price(snap.get("84")),
            "ask": parse_price(snap.get("86")),
        }
    return results


# ---------------------------------------------------------------------------
# Strategy construction
# ---------------------------------------------------------------------------

def build_strategy(spx_price, expiry_date, ratio=2.0):
    print("[3/9] Finding ATM strikes ...")
    lower = int(math.floor(spx_price / STRIKE_INCREMENT) * STRIKE_INCREMENT)
    upper = lower + STRIKE_INCREMENT
    print(f"       SPX={spx_price:.2f} -> Short Put @ {lower}, Short Call @ {upper}")

    print("[4/9] Fetching ATM option contracts ...")
    sp_contract = get_option_contract(lower, "P", expiry_date)
    sc_contract = get_option_contract(upper, "C", expiry_date)
    print(f"       Short Put  conid={sp_contract['conid']} ({sp_contract.get('tradingClass', '?')})")
    print(f"       Short Call conid={sc_contract['conid']} ({sc_contract.get('tradingClass', '?')})")

    print("[5/9] Fetching ATM option prices ...")
    prices = get_option_prices([sp_contract["conid"], sc_contract["conid"]])
    sp_price = prices[sp_contract["conid"]]
    sc_price = prices[sc_contract["conid"]]
    print(f"       Short Put  bid={sp_price['bid']} ask={sp_price['ask']}")
    print(f"       Short Call bid={sc_price['bid']} ask={sc_price['ask']}")

    if sp_price["bid"] is None or sc_price["bid"] is None:
        raise RuntimeError("Could not get bid prices for short legs. Market may be closed.")

    print("[6/9] Calculating wing strikes ...")
    net_credit_shorts = sp_price["bid"] + sc_price["bid"]
    # wing_width = net_credit * (ratio + 1) to achieve max_loss = ratio * max_profit
    wing_width = round_to_strike((ratio + 1.0) * net_credit_shorts)
    if wing_width < STRIKE_INCREMENT:
        wing_width = STRIKE_INCREMENT

    lp_strike = lower - wing_width
    lc_strike = upper + wing_width
    print(f"       Net credit from shorts: {net_credit_shorts:.2f}")
    print(f"       Wing width: {wing_width} -> Long Put @ {lp_strike}, Long Call @ {lc_strike}")

    print("[7/9] Fetching wing option contracts ...")
    lp_contract = get_option_contract(lp_strike, "P", expiry_date)
    lc_contract = get_option_contract(lc_strike, "C", expiry_date)
    print(f"       Long Put  conid={lp_contract['conid']}")
    print(f"       Long Call conid={lc_contract['conid']}")

    print("[8/9] Fetching wing option prices ...")
    wing_prices = get_option_prices([lp_contract["conid"], lc_contract["conid"]])
    lp_price = wing_prices[lp_contract["conid"]]
    lc_price = wing_prices[lc_contract["conid"]]
    print(f"       Long Put  bid={lp_price['bid']} ask={lp_price['ask']}")
    print(f"       Long Call bid={lc_price['bid']} ask={lc_price['ask']}")

    if lp_price["ask"] is None or lc_price["ask"] is None:
        raise RuntimeError("Could not get ask prices for long legs. Market may be closed.")

    print("[9/9] Calculating final strategy ...")
    net_credit = net_credit_shorts - lp_price["ask"] - lc_price["ask"]
    max_profit = net_credit * 100
    max_loss = (wing_width - net_credit) * 100
    ratio = max_loss / max_profit if max_profit > 0 else float("inf")

    return {
        "expiry": str(expiry_date),
        "spx_price": spx_price,
        "legs": [
            {"action": "BUY",  "strike": lp_strike, "right": "P", "conid": lp_contract["conid"],
             "bid": lp_price["bid"], "ask": lp_price["ask"], "label": "Long Put (wing)"},
            {"action": "SELL", "strike": lower,      "right": "P", "conid": sp_contract["conid"],
             "bid": sp_price["bid"], "ask": sp_price["ask"], "label": "Short Put (ATM)"},
            {"action": "SELL", "strike": upper,       "right": "C", "conid": sc_contract["conid"],
             "bid": sc_price["bid"], "ask": sc_price["ask"], "label": "Short Call (ATM)"},
            {"action": "BUY",  "strike": lc_strike,  "right": "C", "conid": lc_contract["conid"],
             "bid": lc_price["bid"], "ask": lc_price["ask"], "label": "Long Call (wing)"},
        ],
        "wing_width": wing_width,
        "net_credit": round(net_credit, 2),
        "max_profit": round(max_profit, 2),
        "max_loss": round(max_loss, 2),
        "ratio": round(ratio, 2),
        "lower_breakeven": round(lower - net_credit, 2),
        "upper_breakeven": round(upper + net_credit, 2),
    }


def display_strategy(strategy, quantity):
    s = strategy
    print("\n" + "=" * 70)
    print("  SPX IRON BUTTERFLY / CONDOR STRATEGY")
    print("=" * 70)
    print(f"  Expiry:       {s['expiry']}")
    print(f"  SPX Price:    {s['spx_price']:.2f}")
    print(f"  Quantity:     {quantity}")
    print("-" * 70)
    print(f"  {'Leg':<22} {'Strike':>7} {'ConID':>12} {'Bid':>8} {'Ask':>8} {'Action':>6}")
    print("-" * 70)
    for leg in s["legs"]:
        bid_s = f"{leg['bid']:.2f}" if leg['bid'] is not None else "N/A"
        ask_s = f"{leg['ask']:.2f}" if leg['ask'] is not None else "N/A"
        print(f"  {leg['label']:<22} {leg['strike']:>7} {leg['conid']:>12} {bid_s:>8} {ask_s:>8} {leg['action']:>6}")
    print("-" * 70)
    print(f"  Wing Width:        {s['wing_width']} points")
    print(f"  Net Credit:        {s['net_credit']:.2f} per spread")
    print(f"  Max Profit:       ${s['max_profit'] * quantity:,.2f}")
    print(f"  Max Loss:         ${s['max_loss'] * quantity:,.2f}")
    print(f"  Risk/Reward:       {s['ratio']:.2f}x  (target ~2.0x)")
    print(f"  Lower Breakeven:   {s['lower_breakeven']:.2f}")
    print(f"  Upper Breakeven:   {s['upper_breakeven']:.2f}")
    print("=" * 70)


def build_order_json(account_id, strategy, quantity):
    """Build the order JSON that submit_order.py can consume."""
    legs = strategy["legs"]
    conidex_parts = []
    for leg in legs:
        ratio = 1 if leg["action"] == "BUY" else -1
        conidex_parts.append(f"{leg['conid']}/{ratio}")

    conidex = f"{SPX_CONID};;;{','.join(conidex_parts)}"
    limit_price = round(-strategy["net_credit"], 2)

    return {
        "account_id": account_id,
        "orders": [
            {
                "conidex": conidex,
                "orderType": "LMT",
                "side": "BUY",
                "price": limit_price,
                "tif": "DAY",
                "quantity": quantity,
            }
        ],
        "metadata": {
            "strategy": "iron_butterfly",
            "symbol": "SPX",
            "expiry": strategy["expiry"],
            "net_credit": strategy["net_credit"],
            "max_profit": strategy["max_profit"],
            "max_loss": strategy["max_loss"],
            "ratio": strategy["ratio"],
            "legs": strategy["legs"],
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build an SPX Iron Butterfly order and save to JSON for submission."
    )
    parser.add_argument("expiry", help='"today", "tomorrow", or YYYY-MM-DD')
    parser.add_argument("--quantity", type=int, default=1, help="Number of contracts (default: 1)")
    parser.add_argument("--ratio", type=float, default=2.0,
                        help="Target max_loss/max_profit ratio (default: 2.0). Lower = tighter wings.")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file path (default: iron_butterfly_<date>.json)")
    parser.add_argument("--submit", action="store_true",
                        help="Immediately submit the order via submit_order.py after building")
    args = parser.parse_args()

    expiry_date = parse_expiry(args.expiry)
    output_file = args.output or f"iron_butterfly_{expiry_date}.json"
    print(f"Target expiry: {expiry_date} ({expiry_date.strftime('%A')})")
    print(f"Quantity:      {args.quantity}")
    print(f"Output:        {output_file}")
    print()

    initialize_session()
    account_id = get_account_id()
    spx_price = get_spx_price()
    strategy = build_strategy(spx_price, expiry_date, ratio=args.ratio)
    display_strategy(strategy, args.quantity)

    order_json = build_order_json(account_id, strategy, args.quantity)
    with open(output_file, "w") as f:
        json.dump(order_json, f, indent=2)
    print(f"\nOrder saved to: {output_file}")

    if args.submit:
        import subprocess
        submit_script = os.path.join(SCRIPT_DIR, "submit_order.py")
        print("\nSubmitting order ...")
        result = subprocess.run([sys.executable, submit_script, output_file, "-y"])
        sys.exit(result.returncode)
    else:
        print(f"To submit:  python3 {os.path.join(SCRIPT_DIR, 'submit_order.py')} {output_file}")


if __name__ == "__main__":
    main()

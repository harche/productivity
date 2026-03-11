"""
IBKR Client Portal API constants — single source of truth.

All scripts and tests should reference these instead of hardcoding strings.
Values here are validated against the live IBKR API.
"""

from __future__ import annotations

# Order types accepted by the Client Portal API
ORDER_TYPES: set[str] = {"LMT", "STP", "STP LMT", "MIDPRICE", "LOC", "MOC"}

# Order sides
SIDES: set[str] = {"BUY", "SELL"}

# Time-in-force values
TIF_VALUES: set[str] = {"DAY", "GTC", "IOC", "OPG"}

# Mapping from order status response values to API-accepted values
ORDER_TYPE_MAP: dict[str, str] = {
    "LIMIT": "LMT", "Limit": "LMT", "LMT": "LMT",
    "MARKET": "MKT", "Market": "MKT", "MKT": "MKT",
    "STP LMT": "STP LMT", "Stop Limit": "STP LMT", "STP_LIMIT": "STP LMT",
    "STOP": "STP", "Stop": "STP", "STP": "STP",
    "MIDPRICE": "MIDPRICE", "MidPrice": "MIDPRICE",
    "LOC": "LOC", "MOC": "MOC",
}

SIDE_MAP: dict[str, str] = {
    "B": "BUY", "BUY": "BUY", "Buy": "BUY",
    "S": "SELL", "SELL": "SELL", "Sell": "SELL",
}

TIF_MAP: dict[str, str] = {
    "CLOSE": "DAY", "DAY": "DAY",
    "GTC": "GTC", "IOC": "IOC", "OPG": "OPG",
}

# Market data snapshot field IDs
FIELD_LAST: str = "31"
FIELD_SYMBOL: str = "55"
FIELD_HIGH: str = "70"
FIELD_LOW: str = "71"
FIELD_CHANGE: str = "82"
FIELD_CHANGE_PCT: str = "83"
FIELD_BID: str = "84"
FIELD_ASK_SIZE: str = "85"
FIELD_ASK: str = "86"
FIELD_VOLUME: str = "87"
FIELD_BID_SIZE: str = "88"

# Greeks fields
FIELD_DELTA: str = "7308"
FIELD_GAMMA: str = "7309"
FIELD_THETA: str = "7310"
FIELD_VEGA: str = "7311"
FIELD_IV: str = "7633"

# Common conids
SPX_CONID: int = 416904
AAPL_CONID: int = 265598

# Strike increment for SPX options
SPX_STRIKE_INCREMENT: int = 5

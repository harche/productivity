#!/usr/bin/env python3
"""
IBKR Client Portal Gateway starter.

Searches common locations for the gateway, starts it, waits for port 5000,
and checks authentication status.

Usage:
    python start_gateway.py
    python start_gateway.py --path /custom/path/to/gateway
"""

import argparse
import os
import socket
import subprocess
import sys
import time

SEARCH_PATHS = [
    os.path.expanduser("~/ibkr"),
    os.path.expanduser("~/clientportal.gw"),
    os.path.expanduser("~/clientportal"),
    os.path.expanduser("~/ib_gateway"),
    os.path.expanduser("~/IBKR"),
]

PORT = 5000
STARTUP_TIMEOUT = 60


def find_gateway():
    for path in SEARCH_PATHS:
        run_sh = os.path.join(path, "bin", "run.sh")
        conf = os.path.join(path, "root", "conf.yaml")
        if os.path.isfile(run_sh) and os.path.isfile(conf):
            return path
    return None


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("localhost", port)) == 0


def check_auth():
    try:
        import urllib.request
        import ssl
        import json
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(f"https://localhost:{PORT}/v1/api/iserver/auth/status")
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            data = json.loads(resp.read())
            return data
    except Exception:
        return None


def auto_login(account):
    """Attempt automated login via login_gateway.py."""
    script = os.path.join(os.path.dirname(__file__), "login_gateway.py")
    if not os.path.isfile(script):
        return
    print(f"\nAttempting auto-login ({account}) ...")
    subprocess.call([sys.executable, script, "--account", account])


def main():
    parser = argparse.ArgumentParser(description="Start the IBKR Client Portal Gateway.")
    parser.add_argument("--path", help="Path to gateway root directory (contains bin/run.sh)")
    parser.add_argument(
        "--login", nargs="?", const="paper", choices=["paper", "live"],
        help="Auto-login after start (default: paper)",
    )
    args = parser.parse_args()

    # Check if already running
    if is_port_open(PORT):
        print(f"Gateway already running on port {PORT}.")
        status = check_auth()
        if status:
            auth = status.get("authenticated", False)
            print(f"  Authenticated: {auth}")
            if not auth:
                if args.login:
                    auto_login(args.login)
                else:
                    print(f"  Log in at: https://localhost:{PORT}")
        return

    # Find gateway
    gw_path = args.path or find_gateway()
    if not gw_path:
        searched = "\n  ".join(SEARCH_PATHS)
        print(f"ERROR: Could not find gateway. Searched:\n  {searched}")
        print("\nSpecify path with: python start_gateway.py --path /path/to/gateway")
        print("Download from: https://www.interactivebrokers.com/en/trading/ib-api.php")
        sys.exit(1)

    run_sh = os.path.join(gw_path, "bin", "run.sh")
    conf = os.path.join(gw_path, "root", "conf.yaml")
    print(f"Found gateway at: {gw_path}")

    # Start gateway (must use relative paths — run.sh prepends ../ to config_file)
    print("Starting gateway ...")
    subprocess.Popen(
        ["bin/run.sh", "root/conf.yaml"],
        cwd=gw_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for port
    print(f"Waiting for port {PORT} ...", end="", flush=True)
    start = time.time()
    while time.time() - start < STARTUP_TIMEOUT:
        if is_port_open(PORT):
            print(" ready.")
            if args.login:
                auto_login(args.login)
            else:
                print(f"\nGateway is running. Log in at: https://localhost:{PORT}")
            return
        print(".", end="", flush=True)
        time.sleep(1)

    print(f"\nERROR: Gateway did not start within {STARTUP_TIMEOUT}s.")
    print("Check that Java is installed: java -version")
    sys.exit(1)


if __name__ == "__main__":
    main()

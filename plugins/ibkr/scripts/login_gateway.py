#!/usr/bin/env python3
"""
IBKR gateway login via Playwright browser automation.

Fetches credentials from macOS Keychain and automates the Client Portal
Gateway login page, including paper/live account selection and 2FA wait.

Usage:
    python login_gateway.py                 # paper account (default)
    python login_gateway.py --account live  # live account
"""

import argparse
import json
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request

GATEWAY_URL = "https://localhost:5000"
AUTH_URL = f"{GATEWAY_URL}/v1/api/iserver/auth/status"
AUTH_POLL_SECONDS = 10  # brief wait after form submit for gateway to register auth


def get_keychain(service):
    """Fetch a password from macOS Keychain."""
    try:
        r = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def check_auth():
    """Check gateway authentication status. Returns dict or None if gateway is down."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(AUTH_URL)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        # 401 = gateway running but session expired/not authenticated
        if e.code == 401:
            return {"authenticated": False, "connected": False}
        return None
    except (urllib.error.URLError, OSError):
        # Connection refused = gateway not running
        return None
    except Exception:
        return None


def pw_run(code, timeout=60):
    """Run playwright-cli run-code and parse the JSON result."""
    r = subprocess.run(
        ["playwright-cli", "run-code", code],
        capture_output=True, text=True, timeout=timeout,
    )
    if r.returncode != 0:
        return {"error": (r.stderr or r.stdout or "playwright-cli failed").strip()[:300]}

    m = re.search(r"### Result\n(.*?)(?:\n###|$)", r.stdout, re.DOTALL)
    if not m:
        return {"error": "Could not parse playwright-cli output"}

    raw = m.group(1).strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        return parsed
    except (json.JSONDecodeError, TypeError):
        return {"error": f"Invalid JSON: {raw[:200]}"}


def cleanup_browser():
    """Close the playwright-cli browser session."""
    subprocess.run(
        ["playwright-cli", "close"],
        capture_output=True, text=True, timeout=5,
    )


def ensure_browser():
    """Make sure a playwright-cli browser session is running."""
    lr = subprocess.run(
        ["playwright-cli", "list"], capture_output=True, text=True, timeout=5,
    )
    has_browser = lr.returncode == 0 and "default" in (lr.stdout or "")
    if not has_browser:
        subprocess.run(
            ["playwright-cli", "open"],
            capture_output=True, text=True, timeout=15,
        )


def submit_credentials(username, password, account_type):
    """Fill and submit the IBKR login form via Playwright."""
    username_js = json.dumps(username)
    password_js = json.dumps(password)
    want_paper = "true" if account_type == "paper" else "false"

    code = (
        "async page => {\n"
        "  const ctx = await page.context().browser().newContext({ ignoreHTTPSErrors: true });\n"
        "  const p = await ctx.newPage();\n"
        "  try {\n"
        '    await p.goto("' + GATEWAY_URL + '", { waitUntil: "networkidle", timeout: 30000 });\n'
        '    await p.waitForSelector("#xyz-field-username", { timeout: 15000 });\n'
        "\n"
        "    // Paper/Live toggle\n"
        "    const wantPaper = " + want_paper + ";\n"
        "    await p.evaluate((wp) => {\n"
        "      const el = document.getElementById('toggle1');\n"
        "      if (el && el.checked !== wp) el.click();\n"
        "    }, wantPaper);\n"
        "    await p.waitForTimeout(500);\n"
        "\n"
        "    // Fill credentials and submit\n"
        '    await p.fill("#xyz-field-username", ' + username_js + ");\n"
        '    await p.fill("#xyz-field-password", ' + password_js + ");\n"
        "    await p.locator('button[type=\"submit\"]:visible').first().click();\n"
        "    await p.waitForTimeout(5000);\n"
        "\n"
        "    const url = p.url();\n"
        "\n"
        "    // If page redirected away from login, credentials were accepted\n"
        '    if (url.includes("/Dispatcher") || url.includes("/portal")) {\n'
        "      await ctx.close();\n"
        '      return JSON.stringify({ submitted: true, twoFactor: "none" });\n'
        "    }\n"
        "\n"
        "    // Still on login page — check for error\n"
        '    let error = "";\n'
        "    try {\n"
        '      const els = await p.$$(".xyz-error");\n'
        "      for (const el of els) {\n"
        "        if (await el.isVisible()) { error = (await el.textContent()).trim(); break; }\n"
        "      }\n"
        "    } catch {}\n"
        "    if (error) {\n"
        "      await ctx.close();\n"
        "      return JSON.stringify({ error });\n"
        "    }\n"
        "\n"
        "    // Detect 2FA type\n"
        '    let twoFactor = "none";\n'
        "    try {\n"
        '      const n = await p.$(".xyz-notificationimg");\n'
        '      if (n && await n.isVisible()) twoFactor = "ibkey";\n'
        "    } catch {}\n"
        '    if (twoFactor === "none") {\n'
        "      try {\n"
        '        const s = await p.$(".xyz-silver-response");\n'
        '        if (s && await s.isVisible()) twoFactor = "sms";\n'
        "      } catch {}\n"
        "    }\n"
        "\n"
        "    // Leave context open for 2FA (closed when browser session closes)\n"
        "    return JSON.stringify({ submitted: true, twoFactor });\n"
        "  } catch (e) {\n"
        "    try { await ctx.close(); } catch {}\n"
        "    return JSON.stringify({ error: e.message });\n"
        "  }\n"
        "}"
    )

    return pw_run(code, timeout=30)


def main():
    parser = argparse.ArgumentParser(description="Login to IBKR gateway.")
    parser.add_argument(
        "--account", choices=["paper", "live"], default="paper",
        help="Account type (default: paper)",
    )
    args = parser.parse_args()

    # Already authenticated?
    status = check_auth()
    if status and status.get("authenticated"):
        print("Already authenticated.")
        return
    if not status:
        print("ERROR: Gateway not running. Start with: python3 start_gateway.py")
        sys.exit(1)

    # Fetch credentials from Keychain
    username = get_keychain(f"ibkr-{args.account}-username")
    password = get_keychain(f"ibkr-{args.account}-password")
    if not username or not password:
        acct = args.account
        print(f"ERROR: IBKR {acct} credentials not in Keychain. Store them with:")
        print(f'  security add-generic-password -a "$USER" -s "ibkr-{acct}-username" -w "USERNAME"')
        print(f'  security add-generic-password -a "$USER" -s "ibkr-{acct}-password" -w "PASSWORD"')
        sys.exit(1)

    # Ensure playwright-cli is available
    if subprocess.run(["which", "playwright-cli"], capture_output=True).returncode != 0:
        print("ERROR: playwright-cli not found.")
        sys.exit(1)

    ensure_browser()

    print(f"Logging in as {username} ({args.account}) ...")

    # Submit credentials
    result = submit_credentials(username, password, args.account)

    if result.get("error"):
        print(f"ERROR: {result['error']}")
        cleanup_browser()
        sys.exit(1)

    # Brief wait for gateway to register auth (paper accounts need no 2FA)
    start = time.time()
    while time.time() - start < AUTH_POLL_SECONDS:
        time.sleep(2)
        status = check_auth()
        if status and status.get("authenticated"):
            print("Login successful.")
            cleanup_browser()
            return

    # Not yet authenticated — 2FA likely required
    print("Credentials submitted. Approve the login on your IB Key app.")
    cleanup_browser()


if __name__ == "__main__":
    main()

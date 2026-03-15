#!/usr/bin/env node
// Extract Reddit bearer token (token_v2) from Chrome's encrypted cookie store.
// Prints the token to stdout for use with curl.
//
// Usage:
//   node get-token.mjs          → prints bearer token
//   node get-token.mjs --check  → prints token + expiry info as JSON
//
// Supports macOS and Linux.

import { execSync, spawnSync } from "child_process";
import {
  readdirSync,
  existsSync,
  copyFileSync,
  unlinkSync,
  rmdirSync,
  mkdtempSync,
} from "fs";
import { join } from "path";
import { createDecipheriv, pbkdf2Sync } from "crypto";
import { homedir, tmpdir, platform } from "os";

const IS_LINUX = platform() === "linux";

const CHROME_BASE = IS_LINUX
  ? join(homedir(), ".config/google-chrome")
  : join(homedir(), "Library/Application Support/Google/Chrome");

const REDDIT_HOSTS = [".reddit.com"];

function fail(msg) {
  process.stderr.write(JSON.stringify({ error: msg }) + "\n");
  process.exit(1);
}

// Find Chrome profile directory that has Reddit cookies
function findRedditProfile() {
  if (!existsSync(CHROME_BASE)) {
    fail("Chrome not found. Expected: " + CHROME_BASE);
  }

  const candidates = [];
  try {
    for (const entry of readdirSync(CHROME_BASE)) {
      if (entry === "Default" || entry.startsWith("Profile ")) {
        candidates.push(entry);
      }
    }
  } catch {}

  if (candidates.length === 0) candidates.push("Default");

  for (const profile of candidates) {
    const cookiesPath = join(CHROME_BASE, profile, "Cookies");
    if (!existsSync(cookiesPath)) continue;

    const tmpDir = mkdtempSync(join(tmpdir(), "rd-check-"));
    const tmpDb = join(tmpDir, "Cookies");
    copyFileSync(cookiesPath, tmpDb);
    for (const ext of ["-wal", "-shm"]) {
      const src = cookiesPath + ext;
      if (existsSync(src)) copyFileSync(src, tmpDb + ext);
    }

    try {
      const hostCond = REDDIT_HOSTS.map((h) => `host_key = '${h}'`).join(
        " OR "
      );
      const result = spawnSync(
        "sqlite3",
        [
          tmpDb,
          `SELECT COUNT(*) FROM cookies WHERE (${hostCond}) AND name = 'token_v2';`,
        ],
        { encoding: "utf-8", timeout: 5000 }
      );
      const count = parseInt((result.stdout || "").trim(), 10);
      if (count > 0) return join(CHROME_BASE, profile);
    } finally {
      for (const ext of ["", "-wal", "-shm"]) {
        try { unlinkSync(tmpDb + ext); } catch {}
      }
      try { rmdirSync(tmpDir); } catch {}
    }
  }

  fail(
    "No Reddit session found in Chrome. Make sure you are logged into reddit.com in Chrome."
  );
}

// Get Chrome Safe Storage password for cookie decryption
function getChromePassword() {
  if (IS_LINUX) {
    try {
      return execSync("secret-tool lookup application chrome", {
        encoding: "utf-8",
      }).trim();
    } catch {
      return "peanuts";
    }
  }
  return execSync(
    'security find-generic-password -s "Chrome Safe Storage" -w',
    { encoding: "utf-8" }
  ).trim();
}

// Decrypt a Chrome cookie value
function decryptCookieValue(encryptedBuf) {
  const prefix = encryptedBuf.subarray(0, 3).toString("utf-8");
  const iterations = IS_LINUX ? 1 : 1003;

  if (prefix !== "v10" && prefix !== "v11") {
    fail(`Unsupported Chrome cookie encryption version "${prefix}".`);
  }

  const password = getChromePassword();
  const key = pbkdf2Sync(password, "saltysalt", iterations, 16, "sha1");
  const iv = Buffer.alloc(16, 0x20);

  const decipher = createDecipheriv("aes-128-cbc", key, iv);
  const decrypted = Buffer.concat([
    decipher.update(encryptedBuf.subarray(3)),
    decipher.final(),
  ]);

  const str = decrypted.toString("latin1");

  // Find longest run of printable ASCII (the actual cookie value)
  let best = "";
  let current = "";
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i);
    if (code >= 0x20 && code < 0x7f) {
      current += str[i];
    } else {
      if (current.length > best.length) best = current;
      current = "";
    }
  }
  if (current.length > best.length) best = current;

  if (best.length > 0) return best;

  return decrypted.subarray(32).toString("utf-8").replace(/[^\x20-\x7e]/g, "");
}

// Extract and decrypt a named cookie from Chrome's Cookies DB
function extractCookie(profileDir, cookieName) {
  const cookiesPath = join(profileDir, "Cookies");
  if (!existsSync(cookiesPath)) {
    fail("Chrome Cookies database not found: " + cookiesPath);
  }

  const tmpDir = mkdtempSync(join(tmpdir(), "rd-cookies-"));
  const tmpDb = join(tmpDir, "Cookies");
  copyFileSync(cookiesPath, tmpDb);
  for (const ext of ["-wal", "-shm"]) {
    const src = cookiesPath + ext;
    if (existsSync(src)) copyFileSync(src, tmpDb + ext);
  }

  try {
    const hostCond = REDDIT_HOSTS.map((h) => `host_key = '${h}'`).join(
      " OR "
    );
    const result = spawnSync(
      "sqlite3",
      [
        tmpDb,
        `SELECT hex(encrypted_value) FROM cookies WHERE (${hostCond}) AND name = '${cookieName}' ORDER BY expires_utc DESC LIMIT 1;`,
      ],
      { encoding: "utf-8", timeout: 5000 }
    );

    const hex = (result.stdout || "").trim();
    if (!hex) {
      fail(
        `Reddit "${cookieName}" cookie not found in Chrome. Make sure you are logged into reddit.com in Chrome.`
      );
    }

    return decryptCookieValue(Buffer.from(hex, "hex"));
  } finally {
    for (const ext of ["", "-wal", "-shm"]) {
      try { unlinkSync(tmpDb + ext); } catch {}
    }
    try { rmdirSync(tmpDir); } catch {}
  }
}

// --- Main ---

const profileDir = findRedditProfile();
let token = extractCookie(profileDir, "token_v2");

// token_v2 is a JWT — ensure it starts at "eyJ" (base64 for '{"')
const jwtStart = token.indexOf("eyJ");
if (jwtStart > 0) {
  token = token.substring(jwtStart);
} else if (jwtStart < 0) {
  fail("Extracted token_v2 does not contain a valid JWT.");
}

if (process.argv.includes("--check")) {
  // Decode JWT payload to show expiry
  try {
    const payload = JSON.parse(
      Buffer.from(token.split(".")[1], "base64").toString()
    );
    const expiresAt = new Date(payload.exp * 1000);
    const remainingMin = Math.round((payload.exp - Date.now() / 1000) / 60);
    process.stdout.write(
      JSON.stringify(
        {
          status: remainingMin > 0 ? "valid" : "expired",
          expires_at: expiresAt.toISOString(),
          remaining_minutes: remainingMin,
          user: payload.lid || payload.sub,
        },
        null,
        2
      ) + "\n"
    );
  } catch {
    process.stdout.write(
      JSON.stringify({ status: "ok", token_length: token.length }) + "\n"
    );
  }
} else {
  process.stdout.write(token);
}

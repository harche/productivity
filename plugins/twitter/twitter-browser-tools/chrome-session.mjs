// Extract Twitter/X session (auth_token + ct0) directly from Chrome's cookie store.
// No Playwright or browser automation required.
//
// auth_token: session cookie for authentication
// ct0: CSRF token used in x-csrf-token header

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
import { homedir, tmpdir } from "os";

const CHROME_BASE = join(
  homedir(),
  "Library/Application Support/Google/Chrome"
);

const TWITTER_HOSTS = [".x.com", ".twitter.com"];

// Find Chrome profile directory that has Twitter cookies
function findTwitterProfile() {
  if (!existsSync(CHROME_BASE)) {
    throw new Error("Chrome not found. Expected: " + CHROME_BASE);
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

    const tmpDir = mkdtempSync(join(tmpdir(), "tw-check-"));
    const tmpDb = join(tmpDir, "Cookies");
    copyFileSync(cookiesPath, tmpDb);
    for (const ext of ["-wal", "-shm"]) {
      const src = cookiesPath + ext;
      if (existsSync(src)) copyFileSync(src, tmpDb + ext);
    }

    try {
      const hostCond = TWITTER_HOSTS.map((h) => `host_key = '${h}'`).join(
        " OR "
      );
      const result = spawnSync(
        "sqlite3",
        [
          tmpDb,
          `SELECT COUNT(*) FROM cookies WHERE (${hostCond}) AND name = 'auth_token';`,
        ],
        { encoding: "utf-8", timeout: 5000 }
      );
      const count = parseInt((result.stdout || "").trim(), 10);
      if (count > 0) return join(CHROME_BASE, profile);
    } finally {
      for (const ext of ["", "-wal", "-shm"]) {
        try {
          unlinkSync(tmpDb + ext);
        } catch {}
      }
      try {
        rmdirSync(tmpDir);
      } catch {}
    }
  }

  throw new Error(
    "No Twitter/X session found in Chrome. Make sure you are logged into X (twitter.com) in Chrome."
  );
}

// Decrypt a Chrome cookie value (macOS: v10 prefix, AES-128-CBC, Keychain password)
function decryptCookieValue(encryptedBuf) {
  const prefix = encryptedBuf.subarray(0, 3).toString("utf-8");
  if (prefix !== "v10") {
    throw new Error(
      `Unsupported Chrome cookie encryption version "${prefix}". Only macOS v10 is supported.`
    );
  }

  const password = execSync(
    'security find-generic-password -s "Chrome Safe Storage" -w',
    { encoding: "utf-8" }
  ).trim();

  const key = pbkdf2Sync(password, "saltysalt", 1003, 16, "sha1");
  const iv = Buffer.alloc(16, 0x20);

  const decipher = createDecipheriv("aes-128-cbc", key, iv);
  const decrypted = Buffer.concat([
    decipher.update(encryptedBuf.subarray(3)),
    decipher.final(),
  ]);

  // Chrome may prepend a binary header to the cookie value before encrypting.
  // Try to find the actual cookie value by looking for printable ASCII runs.
  // auth_token is 40 hex chars, ct0 is a long alphanumeric string.
  const str = decrypted.toString("latin1");

  // Find the longest run of printable ASCII characters (the actual cookie value)
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

  // Fallback: skip the 32-byte Chrome header
  return decrypted.subarray(32).toString("utf-8").replace(/[^\x20-\x7e]/g, "");
}

// Extract and decrypt a named cookie from Chrome's Cookies DB
function extractCookie(profileDir, cookieName) {
  const cookiesPath = join(profileDir, "Cookies");
  if (!existsSync(cookiesPath)) {
    throw new Error("Chrome Cookies database not found: " + cookiesPath);
  }

  const tmpDir = mkdtempSync(join(tmpdir(), "tw-cookies-"));
  const tmpDb = join(tmpDir, "Cookies");
  copyFileSync(cookiesPath, tmpDb);
  for (const ext of ["-wal", "-shm"]) {
    const src = cookiesPath + ext;
    if (existsSync(src)) copyFileSync(src, tmpDb + ext);
  }

  try {
    const hostCond = TWITTER_HOSTS.map((h) => `host_key = '${h}'`).join(
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
      throw new Error(
        `Twitter "${cookieName}" cookie not found in Chrome. Make sure you are logged into X in Chrome.`
      );
    }

    return decryptCookieValue(Buffer.from(hex, "hex"));
  } finally {
    for (const ext of ["", "-wal", "-shm"]) {
      try {
        unlinkSync(tmpDb + ext);
      } catch {}
    }
    try {
      rmdirSync(tmpDir);
    } catch {}
  }
}

// Cached session for the lifetime of this process
let cachedSession = null;

export function getTwitterSession() {
  if (cachedSession) return cachedSession;

  const profileDir = findTwitterProfile();
  const authToken = extractCookie(profileDir, "auth_token");
  const ct0 = extractCookie(profileDir, "ct0");

  cachedSession = { authToken, ct0 };
  return cachedSession;
}

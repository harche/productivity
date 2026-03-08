// Extract Slack session (token + cookie) directly from Chrome's local storage.
// No Playwright or browser automation required.
//
// Token: read from Chrome's LevelDB localStorage files (xoxc-* pattern)
// Cookie: read + decrypt the 'd' cookie from Chrome's SQLite Cookies DB
//
// Supports macOS and Linux.

import { execSync, spawnSync } from "child_process";
import {
  readdirSync,
  readFileSync,
  copyFileSync,
  unlinkSync,
  existsSync,
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

// Find Chrome profile directory that has Slack data
function findSlackProfile() {
  if (!existsSync(CHROME_BASE)) {
    throw new Error(
      "Chrome not found. Expected: " + CHROME_BASE
    );
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
    const lsDir = join(CHROME_BASE, profile, "Local Storage/leveldb");
    if (!existsSync(lsDir)) continue;

    const files = readdirSync(lsDir).filter(
      (f) => f.endsWith(".ldb") || f.endsWith(".log")
    );
    for (const file of files) {
      try {
        const buf = readFileSync(join(lsDir, file));
        if (buf.indexOf("xoxc-") !== -1) {
          return join(CHROME_BASE, profile);
        }
      } catch {}
    }
  }

  throw new Error(
    "No Slack session found in Chrome. Make sure you are logged into Slack in Chrome."
  );
}

// Extract xoxc- token from Chrome's LevelDB localStorage files
function extractToken(profileDir) {
  const lsDir = join(profileDir, "Local Storage/leveldb");
  const files = readdirSync(lsDir).filter(
    (f) => f.endsWith(".ldb") || f.endsWith(".log")
  );

  const tokens = new Set();
  for (const file of files) {
    try {
      // Read as latin1 to preserve all bytes while allowing regex matching
      const str = readFileSync(join(lsDir, file), "latin1");
      for (const m of str.matchAll(/xoxc-[a-zA-Z0-9-]+/g)) {
        tokens.add(m[0]);
      }
    } catch {}
  }

  if (tokens.size === 0) {
    throw new Error(
      "No Slack token found in Chrome localStorage. Make sure you are logged into Slack in Chrome."
    );
  }

  // Return the longest token (shorter matches may be truncated across file boundaries)
  return [...tokens].sort((a, b) => b.length - a.length)[0];
}

// Get Chrome Safe Storage password for cookie decryption.
// macOS: from Keychain. Linux: from GNOME Keyring via secret-tool, fallback to "peanuts".
function getChromePassword() {
  if (IS_LINUX) {
    try {
      return execSync(
        'secret-tool lookup application chrome',
        { encoding: "utf-8" }
      ).trim();
    } catch {
      // Chrome falls back to "peanuts" when no keyring is available
      return "peanuts";
    }
  }
  return execSync(
    'security find-generic-password -s "Chrome Safe Storage" -w',
    { encoding: "utf-8" }
  ).trim();
}

// Decrypt a Chrome cookie value.
// macOS: v10 prefix, 1003 PBKDF2 iterations.
// Linux: v10 or v11 prefix, 1 PBKDF2 iteration.
function decryptCookieValue(encryptedBuf) {
  const prefix = encryptedBuf.subarray(0, 3).toString("utf-8");
  const iterations = IS_LINUX ? 1 : 1003;

  if (prefix !== "v10" && prefix !== "v11") {
    throw new Error(
      `Unsupported Chrome cookie encryption version "${prefix}".`
    );
  }

  const password = getChromePassword();
  const key = pbkdf2Sync(password, "saltysalt", iterations, 16, "sha1");
  const iv = Buffer.alloc(16, 0x20);

  const decipher = createDecipheriv("aes-128-cbc", key, iv);
  const decrypted = Buffer.concat([
    decipher.update(encryptedBuf.subarray(3)),
    decipher.final(),
  ]);

  // Chrome prepends a 32-byte header (hash/metadata) to the cookie value
  // before encrypting. Find the actual xoxd- cookie value in the buffer.
  const marker = Buffer.from("xoxd-");
  const offset = decrypted.indexOf(marker);
  if (offset >= 0) {
    return decrypted.subarray(offset).toString("utf-8");
  }

  // Fallback: skip the 32-byte header directly
  return decrypted.subarray(32).toString("utf-8");
}

// Extract and decrypt the Slack 'd' cookie from Chrome's Cookies DB
function extractCookie(profileDir) {
  const cookiesPath = join(profileDir, "Cookies");
  if (!existsSync(cookiesPath)) {
    throw new Error("Chrome Cookies database not found: " + cookiesPath);
  }

  // Copy DB + WAL/SHM to a temp dir (Chrome holds a lock on the originals)
  const tmpDir = mkdtempSync(join(tmpdir(), "slack-cookies-"));
  const tmpDb = join(tmpDir, "Cookies");
  copyFileSync(cookiesPath, tmpDb);
  for (const ext of ["-wal", "-shm"]) {
    const src = cookiesPath + ext;
    if (existsSync(src)) copyFileSync(src, tmpDb + ext);
  }

  try {
    const result = spawnSync(
      "sqlite3",
      [
        tmpDb,
        `SELECT hex(encrypted_value) FROM cookies WHERE host_key LIKE '%.slack.com' AND name = 'd' ORDER BY expires_utc DESC LIMIT 1;`,
      ],
      { encoding: "utf-8", timeout: 5000 }
    );

    const hex = (result.stdout || "").trim();
    if (!hex) {
      throw new Error(
        'Slack "d" cookie not found in Chrome. Make sure you are logged into Slack in Chrome.'
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

export function getSlackSession() {
  if (cachedSession) return cachedSession;

  const profileDir = findSlackProfile();
  const token = extractToken(profileDir);
  const cookie = extractCookie(profileDir);

  cachedSession = { token, cookie: `d=${cookie}` };
  return cachedSession;
}

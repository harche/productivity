#!/usr/bin/env node
// Unified Slack CLI — reads auth from Chrome's local storage (preferred),
// falls back to Playwright browser injection if Chrome extraction fails.
//
// Usage:
//   node slack.mjs init
//   node slack.mjs history <channelId> [limit]
//   node slack.mjs thread <channelId> <threadTs>
//   node slack.mjs search <query> [count]
//   node slack.mjs channels
//   node slack.mjs channel-info <channelId>
//   node slack.mjs users [limit]
//   node slack.mjs user-info <userId>
//   node slack.mjs send <channelId> <text> [threadTs]
//   node slack.mjs react <channelId> <messageTs> <emoji>
//   node slack.mjs url <slackUrl>

import { readFileSync } from "fs";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// --- Backend selection: Chrome (direct) vs Playwright (fallback) ---

let backend = null; // "chrome" or "playwright"
let chromeSession = null;

async function ensureBackend() {
  if (backend) return;

  try {
    const mod = await import("./chrome-session.mjs");
    chromeSession = mod.getSlackSession();
    backend = "chrome";
    return;
  } catch (e) {
    // Chrome extraction failed — fall back to Playwright
  }

  const check = spawnSync("which", ["playwright-cli"], { encoding: "utf-8" });
  if (check.status !== 0) {
    throw new Error(
      "Could not extract Slack session from Chrome, and playwright-cli is not installed.\n" +
        "Either log into Slack in Chrome, or run: playwright-cli open --extension"
    );
  }

  backend = "playwright";
}

// --- Direct API caller (Chrome backend) ---

let lastCallTime = 0;

async function directSlackApi(method, params = {}) {
  // Rate limiting — random delay between 800-1500ms
  const now = Date.now();
  const delay = 800 + Math.floor(Math.random() * 700);
  const wait = Math.max(0, delay - (now - lastCallTime));
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastCallTime = Date.now();

  const body = new URLSearchParams();
  body.set("token", chromeSession.token);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) body.set(k, String(v));
  }

  const res = await fetch(`https://slack.com/api/${method}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Cookie: chromeSession.cookie,
    },
    body: body.toString(),
  });

  if (res.status === 429) {
    const retryAfter = parseInt(res.headers.get("Retry-After") || "10", 10);
    await new Promise((r) => setTimeout(r, retryAfter * 1000));
    return directSlackApi(method, params);
  }

  return res.json();
}

// --- Playwright backend (fallback) ---

function runInBrowser(evalFn, args) {
  const runCode = `async page => {
    const args = ${JSON.stringify(args || null)};
    const result = await page.evaluate(async (args) => {
      ${evalFn}
    }, args);
    return JSON.stringify(result);
  }`;

  const proc = spawnSync("playwright-cli", ["run-code", runCode], {
    encoding: "utf-8",
    timeout: 60000,
  });

  if (proc.status !== 0) {
    const err = proc.stderr || proc.stdout || "Unknown error";
    if (err.includes("No browser session")) {
      console.error(
        "ERROR: No browser connected. Run: playwright-cli open --extension"
      );
    } else {
      console.error("ERROR:", err.trim());
    }
    process.exit(1);
  }

  const output = proc.stdout;
  const match = output.match(/### Result\n([\s\S]*?)(?:\n###|$)/);
  if (!match) {
    console.error("ERROR: Could not parse playwright-cli output");
    console.error(output);
    process.exit(1);
  }

  try {
    return JSON.parse(JSON.parse(match[1].trim()));
  } catch {
    try {
      return JSON.parse(match[1].trim());
    } catch {
      return match[1].trim();
    }
  }
}

function ensurePlaywrightInit() {
  const checkCode = `async page => {
    const ready = await page.evaluate(() => typeof window.__slack !== "undefined" && !!window.__slack.token);
    return JSON.stringify(ready);
  }`;
  const checkProc = spawnSync("playwright-cli", ["run-code", checkCode], {
    encoding: "utf-8",
    timeout: 10000,
  });
  const checkOut = checkProc.stdout || "";
  if (checkOut.includes("true")) return;

  const script = readFileSync(join(__dirname, "slack-client.js"), "utf-8");
  const runCode = `async page => {
    const script = ${JSON.stringify(script)};
    const result = await page.evaluate(script);
    return JSON.stringify(result);
  }`;

  const proc = spawnSync("playwright-cli", ["run-code", runCode], {
    encoding: "utf-8",
    timeout: 30000,
  });

  if (proc.status !== 0) {
    const err = proc.stderr || proc.stdout || "Unknown error";
    if (err.includes("No browser session")) {
      console.error(
        "ERROR: No browser connected. Run: playwright-cli open --extension"
      );
    } else {
      console.error("ERROR: Init failed —", err.trim());
    }
    process.exit(1);
  }
}

function playwrightSlackCall(slackMethod, params) {
  return runInBrowser(
    `if (!window.__slack) throw new Error("not initialized");
     return await window.__slack.call(args.method, args.params);`,
    { method: slackMethod, params }
  );
}

function playwrightSlackPaginatedCall(slackMethod, params, maxPages) {
  return runInBrowser(
    `if (!window.__slack) throw new Error("not initialized");
     return await window.__slack.callPaginated(args.method, args.params, args.maxPages);`,
    { method: slackMethod, params, maxPages }
  );
}

// --- Unified API interface ---

async function slackApi(method, params = {}) {
  if (backend === "chrome") {
    return directSlackApi(method, params);
  }
  ensurePlaywrightInit();
  return playwrightSlackCall(method, params);
}

async function slackApiPaginated(method, params = {}, maxPages = 5) {
  if (backend === "chrome") {
    let allItems = [];
    let cursor;
    let pages = 0;

    do {
      const p = { ...params };
      if (cursor) p.cursor = cursor;
      const result = await directSlackApi(method, p);

      if (!result.ok) return result;

      for (const key of [
        "channels",
        "members",
        "messages",
        "users",
        "matches",
        "items",
      ]) {
        if (result[key]) {
          const items = Array.isArray(result[key])
            ? result[key]
            : result[key].matches || [];
          allItems.push(...items);
        }
      }

      cursor = result.response_metadata?.next_cursor || undefined;
      if (cursor === "") cursor = undefined;
      pages++;

      if (cursor && pages < maxPages) {
        await new Promise((r) =>
          setTimeout(r, 300 + Math.floor(Math.random() * 700))
        );
      }
    } while (cursor && pages < maxPages);

    return { ok: true, items: allItems, count: allItems.length, pages };
  }

  // Playwright path
  ensurePlaywrightInit();
  return playwrightSlackPaginatedCall(method, params, maxPages);
}

// --- URL parser ---

function parseSlackUrl(url) {
  const parsed = new URL(url);
  const path = parsed.pathname;

  const archivesMatch = path.match(/\/archives\/([A-Z0-9]+)(?:\/p(\d+))?/);
  const clientMatch = path.match(/\/client\/[A-Z0-9]+\/([A-Z0-9]+)/);

  let channelId = null;
  let messageTs = null;
  let threadTs = parsed.searchParams.get("thread_ts") || null;

  if (archivesMatch) {
    channelId = archivesMatch[1];
    if (archivesMatch[2]) {
      const raw = archivesMatch[2];
      if (raw.length >= 10) {
        messageTs =
          raw.substring(0, 10) + "." + raw.substring(10).padEnd(6, "0");
      }
    }
  } else if (clientMatch) {
    channelId = clientMatch[1];
  }

  return { channelId, messageTs, threadTs: threadTs || messageTs };
}

// --- Format helpers ---

function formatMessage(m) {
  let text = m.text || "";
  text = text.replace(/<@([A-Z0-9]+)>/g, "@$1");
  text = text.replace(/<#([A-Z0-9]+)\|([^>]+)>/g, "#$2");
  text = text.replace(/<#([A-Z0-9]+)>/g, "#$1");
  text = text.replace(/<(https?:[^|>]+)\|([^>]+)>/g, "[$2]($1)");
  text = text.replace(/<(https?:[^>]+)>/g, "$1");
  text = text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
  return {
    user: m.user,
    text,
    ts: m.ts,
    thread_ts: m.thread_ts,
    reply_count: m.reply_count,
  };
}

function formatChannel(c) {
  return {
    id: c.id,
    name: c.name,
    topic: c.topic ? c.topic.value : "",
    purpose: c.purpose ? c.purpose.value : "",
    members: c.num_members,
    is_private: c.is_private,
  };
}

function formatUser(u) {
  return {
    id: u.id,
    name: u.name,
    real_name: u.real_name || u.profile?.real_name || "",
    display_name: u.profile?.display_name || "",
    is_bot: u.is_bot,
  };
}

// --- Enterprise Grid restricted methods ---
const RESTRICTED_METHODS = {
  "conversations.list":
    'Use "search" command instead (e.g., search "in:#channel" or search "to:me")',
  "conversations.open":
    'Use "search" command to find DMs (e.g., search "from:@username")',
  "users.conversations":
    'Use "search" command instead (e.g., search "in:#channel")',
};

// --- Commands ---

const [, , command, ...args] = process.argv;

async function main() {
  await ensureBackend();

  switch (command) {
    case "init": {
      const data = await slackApi("auth.test");
      if (!data.ok) {
        console.error("Auth failed:", data.error);
        process.exit(1);
      }
      console.log(
        JSON.stringify(
          {
            ok: true,
            user: data.user,
            team: data.team,
            user_id: data.user_id,
            team_id: data.team_id,
            backend,
          },
          null,
          2
        )
      );
      break;
    }

    case "history": {
      const channelId = args[0];
      const limit = parseInt(args[1]) || 20;
      if (!channelId) {
        console.error("Usage: slack.mjs history <channelId> [limit]");
        process.exit(1);
      }
      const data = await slackApi("conversations.history", {
        channel: channelId,
        limit,
      });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(
        JSON.stringify((data.messages || []).map(formatMessage), null, 2)
      );
      break;
    }

    case "thread": {
      const channelId = args[0];
      const threadTs = args[1];
      if (!channelId || !threadTs) {
        console.error("Usage: slack.mjs thread <channelId> <threadTs>");
        process.exit(1);
      }
      const data = await slackApi("conversations.replies", {
        channel: channelId,
        ts: threadTs,
        limit: 100,
      });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(
        JSON.stringify((data.messages || []).map(formatMessage), null, 2)
      );
      break;
    }

    case "search": {
      const query = args[0];
      const count = parseInt(args[1]) || 20;
      if (!query) {
        console.error("Usage: slack.mjs search <query> [count]");
        process.exit(1);
      }
      const data = await slackApi("search.messages", {
        query,
        count,
        sort: "timestamp",
        sort_dir: "desc",
      });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      const matches = (data.messages?.matches || []).map((m) => ({
        ...formatMessage(m),
        channel: m.channel?.name || "unknown",
        username: m.username,
      }));
      console.log(
        JSON.stringify(
          { total: data.messages?.total || 0, matches },
          null,
          2
        )
      );
      break;
    }

    case "channels": {
      const data = await slackApiPaginated("conversations.list", {
        types: args[0] || "public_channel,private_channel",
        exclude_archived: true,
        limit: 200,
      });
      if (!data.ok) {
        if (data.error === "enterprise_is_restricted") {
          console.error(
            'ERROR: "conversations.list" is restricted on this Enterprise Grid workspace.'
          );
          console.error(
            'Use the "search" command instead (e.g., search "in:#channel-name").'
          );
          process.exit(1);
        }
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(
        JSON.stringify((data.items || []).map(formatChannel), null, 2)
      );
      break;
    }

    case "channel-info": {
      const channelId = args[0];
      if (!channelId) {
        console.error("Usage: slack.mjs channel-info <channelId>");
        process.exit(1);
      }
      const data = await slackApi("conversations.info", {
        channel: channelId,
      });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(JSON.stringify(formatChannel(data.channel), null, 2));
      break;
    }

    case "users": {
      const limit = parseInt(args[0]) || 100;
      const data = await slackApiPaginated("users.list", { limit });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(
        JSON.stringify((data.items || []).map(formatUser), null, 2)
      );
      break;
    }

    case "user-info": {
      const userId = args[0];
      if (!userId) {
        console.error("Usage: slack.mjs user-info <userId>");
        process.exit(1);
      }
      const data = await slackApi("users.info", { user: userId });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(JSON.stringify(formatUser(data.user), null, 2));
      break;
    }

    case "send": {
      const channelId = args[0];
      const text = args[1];
      const threadTs = args[2] || null;
      if (!channelId || !text) {
        console.error("Usage: slack.mjs send <channelId> <text> [threadTs]");
        process.exit(1);
      }
      const params = { channel: channelId, text };
      if (threadTs) params.thread_ts = threadTs;
      const data = await slackApi("chat.postMessage", params);
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(
        JSON.stringify(
          { ok: true, ts: data.ts, channel: data.channel },
          null,
          2
        )
      );
      break;
    }

    case "react": {
      const channelId = args[0];
      const messageTs = args[1];
      const emoji = args[2];
      if (!channelId || !messageTs || !emoji) {
        console.error("Usage: slack.mjs react <channelId> <messageTs> <emoji>");
        process.exit(1);
      }
      const data = await slackApi("reactions.add", {
        channel: channelId,
        timestamp: messageTs,
        name: emoji,
      });
      if (!data.ok) {
        console.error("API error:", data.error);
        process.exit(1);
      }
      console.log(JSON.stringify({ ok: true }, null, 2));
      break;
    }

    case "url": {
      const url = args[0];
      if (!url) {
        console.error("Usage: slack.mjs url <slackUrl>");
        process.exit(1);
      }
      const { channelId, threadTs } = parseSlackUrl(url);
      if (!channelId) {
        console.error("Could not parse channel ID from URL:", url);
        process.exit(1);
      }

      // Get channel info
      const info = await slackApi("conversations.info", {
        channel: channelId,
      });
      const channelName =
        info.ok && info.channel ? info.channel.name : channelId;

      let messages;
      let type;
      if (threadTs) {
        type = "thread";
        const data = await slackApi("conversations.replies", {
          channel: channelId,
          ts: threadTs,
          limit: 100,
        });
        if (!data.ok) {
          console.error("API error:", data.error);
          process.exit(1);
        }
        messages = (data.messages || []).map(formatMessage);
      } else {
        type = "channel_history";
        const data = await slackApi("conversations.history", {
          channel: channelId,
          limit: 20,
        });
        if (!data.ok) {
          console.error("API error:", data.error);
          process.exit(1);
        }
        messages = (data.messages || []).map(formatMessage);
      }

      console.log(
        JSON.stringify(
          { type, channel: channelName, channelId, messages },
          null,
          2
        )
      );
      break;
    }

    case "api": {
      const method = args[0];
      if (!method) {
        console.error("Usage: slack.mjs api <method> [json-params]");
        process.exit(1);
      }
      if (RESTRICTED_METHODS[method]) {
        console.error(
          `ERROR: "${method}" is restricted on Enterprise Grid workspaces.`
        );
        console.error(`Suggestion: ${RESTRICTED_METHODS[method]}`);
        process.exit(1);
      }
      const params = args[1] ? JSON.parse(args[1]) : {};
      const data = await slackApi(method, params);
      if (!data.ok && data.error === "enterprise_is_restricted") {
        console.error(
          `ERROR: "${method}" is restricted on this Enterprise Grid workspace.`
        );
        console.error('Use the "search" command as an alternative.');
        process.exit(1);
      }
      console.log(JSON.stringify(data, null, 2));
      break;
    }

    default:
      console.error(`Slack CLI

Usage: node slack.mjs <command> [args...]

Commands:
  init                              Verify auth, show current user/team
  url <slackUrl>                    Parse URL and fetch content
  history <channelId> [limit]       Read channel messages
  thread <channelId> <threadTs>     Read thread replies
  search <query> [count]            Search messages
  channels                          List channels
  channel-info <channelId>          Get channel details
  users [limit]                     List users
  user-info <userId>                Get user details
  send <channelId> <text> [threadTs]  Send a message
  react <channelId> <ts> <emoji>    Add reaction
  api <method> [jsonParams]         Call any Slack API method`);
      process.exit(command ? 1 : 0);
  }
}

main().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});

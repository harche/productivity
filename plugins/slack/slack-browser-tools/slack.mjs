#!/usr/bin/env node
// Unified Slack CLI — all browser interaction goes through this file.
// Uses spawnSync to avoid shell escaping issues entirely.
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
const CLIENT_SCRIPT = readFileSync(join(__dirname, "slack-client.js"), "utf-8");

// --- Playwright CLI wrapper ---

function runInBrowser(evalFn, args) {
  // evalFn is a string containing an async function body that receives `args`
  // It runs inside page.evaluate() in the browser context
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

  // Extract JSON result from playwright-cli output
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
    // Sometimes the result is a plain string, not double-encoded
    try {
      return JSON.parse(match[1].trim());
    } catch {
      return match[1].trim();
    }
  }
}

// --- Ensure client is initialized ---

function ensureInit() {
  // Quick check first — avoids an unnecessary auth.test API call
  const checkCode = `async page => {
    const ready = await page.evaluate(() => typeof window.__slack !== "undefined" && !!window.__slack.token);
    return JSON.stringify(ready);
  }`;
  const checkProc = spawnSync("playwright-cli", ["run-code", checkCode], {
    encoding: "utf-8",
    timeout: 10000,
  });
  const checkOut = checkProc.stdout || "";
  if (checkOut.includes("true")) {
    return { initialized: true, cached: true };
  }

  // Not initialized — inject the full client
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

  const output = proc.stdout;
  const match = output.match(/### Result\n([\s\S]*?)(?:\n###|$)/);
  if (match) {
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
  return null;
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
        messageTs = raw.substring(0, 10) + "." + raw.substring(10).padEnd(6, "0");
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
  // Clean up Slack markup
  text = text.replace(/<@([A-Z0-9]+)>/g, "@$1");
  text = text.replace(/<#([A-Z0-9]+)\|([^>]+)>/g, "#$2");
  text = text.replace(/<#([A-Z0-9]+)>/g, "#$1");
  text = text.replace(/<(https?:[^|>]+)\|([^>]+)>/g, "[$2]($1)");
  text = text.replace(/<(https?:[^>]+)>/g, "$1");
  text = text.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
  return { user: m.user, text, ts: m.ts, thread_ts: m.thread_ts, reply_count: m.reply_count };
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
// These API methods fail with `enterprise_is_restricted` on Enterprise Grid
// workspaces when using browser session tokens.
const RESTRICTED_METHODS = {
  "conversations.list": 'Use "search" command instead (e.g., search "in:#channel" or search "to:me")',
  "conversations.open": 'Use "search" command to find DMs (e.g., search "from:@username")',
  "users.conversations": 'Use "search" command instead (e.g., search "in:#channel")',
};

// --- Commands ---

const [, , command, ...args] = process.argv;

async function main() {
  switch (command) {
    case "init": {
      const result = ensureInit();
      console.log(JSON.stringify(result, null, 2));
      break;
    }

    case "history": {
      const channelId = args[0];
      const limit = parseInt(args[1]) || 20;
      if (!channelId) { console.error("Usage: slack.mjs history <channelId> [limit]"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.history(args.ch, args.lim);`,
        { ch: channelId, lim: limit }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      const messages = (data.messages || []).map(formatMessage);
      console.log(JSON.stringify(messages, null, 2));
      break;
    }

    case "thread": {
      const channelId = args[0];
      const threadTs = args[1];
      if (!channelId || !threadTs) { console.error("Usage: slack.mjs thread <channelId> <threadTs>"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.thread(args.ch, args.ts);`,
        { ch: channelId, ts: threadTs }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      const messages = (data.messages || []).map(formatMessage);
      console.log(JSON.stringify(messages, null, 2));
      break;
    }

    case "search": {
      const query = args[0];
      const count = parseInt(args[1]) || 20;
      if (!query) { console.error("Usage: slack.mjs search <query> [count]"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.search(args.q, args.c);`,
        { q: query, c: count }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      const matches = (data.messages?.matches || []).map(m => ({
        ...formatMessage(m),
        channel: m.channel?.name || "unknown",
        username: m.username,
      }));
      console.log(JSON.stringify({ total: data.messages?.total || 0, matches }, null, 2));
      break;
    }

    case "channels": {
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.channels(args.types);`,
        { types: args[0] || null }
      );
      if (!data.ok) {
        if (data.error === "enterprise_is_restricted") {
          console.error('ERROR: "conversations.list" is restricted on this Enterprise Grid workspace.');
          console.error('Use the "search" command instead (e.g., search "in:#channel-name").');
          process.exit(1);
        }
        console.error("API error:", data.error); process.exit(1);
      }
      const channels = (data.items || []).map(formatChannel);
      console.log(JSON.stringify(channels, null, 2));
      break;
    }

    case "channel-info": {
      const channelId = args[0];
      if (!channelId) { console.error("Usage: slack.mjs channel-info <channelId>"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.channelInfo(args.ch);`,
        { ch: channelId }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      console.log(JSON.stringify(formatChannel(data.channel), null, 2));
      break;
    }

    case "users": {
      const limit = parseInt(args[0]) || 100;
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.users(args.lim);`,
        { lim: limit }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      const users = (data.items || []).map(formatUser);
      console.log(JSON.stringify(users, null, 2));
      break;
    }

    case "user-info": {
      const userId = args[0];
      if (!userId) { console.error("Usage: slack.mjs user-info <userId>"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.userInfo(args.uid);`,
        { uid: userId }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      console.log(JSON.stringify(formatUser(data.user), null, 2));
      break;
    }

    case "send": {
      const channelId = args[0];
      const text = args[1];
      const threadTs = args[2] || null;
      if (!channelId || !text) { console.error("Usage: slack.mjs send <channelId> <text> [threadTs]"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.send(args.ch, args.text, args.ts);`,
        { ch: channelId, text, ts: threadTs }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      console.log(JSON.stringify({ ok: true, ts: data.ts, channel: data.channel }, null, 2));
      break;
    }

    case "react": {
      const channelId = args[0];
      const messageTs = args[1];
      const emoji = args[2];
      if (!channelId || !messageTs || !emoji) { console.error("Usage: slack.mjs react <channelId> <messageTs> <emoji>"); process.exit(1); }
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.react(args.ch, args.ts, args.emoji);`,
        { ch: channelId, ts: messageTs, emoji }
      );
      if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
      console.log(JSON.stringify({ ok: true }, null, 2));
      break;
    }

    case "url": {
      const url = args[0];
      if (!url) { console.error("Usage: slack.mjs url <slackUrl>"); process.exit(1); }
      const { channelId, threadTs } = parseSlackUrl(url);
      if (!channelId) { console.error("Could not parse channel ID from URL:", url); process.exit(1); }

      ensureInit();

      // Get channel info
      const info = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.channelInfo(args.ch);`,
        { ch: channelId }
      );
      const channelName = info.ok && info.channel ? info.channel.name : channelId;

      let messages;
      let type;
      if (threadTs) {
        type = "thread";
        const data = runInBrowser(
          `if (!window.__slack) throw new Error("not initialized");
           return await window.__slack.thread(args.ch, args.ts);`,
          { ch: channelId, ts: threadTs }
        );
        if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
        messages = (data.messages || []).map(formatMessage);
      } else {
        type = "channel_history";
        const data = runInBrowser(
          `if (!window.__slack) throw new Error("not initialized");
           return await window.__slack.history(args.ch, 20);`,
          { ch: channelId }
        );
        if (!data.ok) { console.error("API error:", data.error); process.exit(1); }
        messages = (data.messages || []).map(formatMessage);
      }

      console.log(JSON.stringify({ type, channel: channelName, channelId, messages }, null, 2));
      break;
    }

    case "api": {
      const method = args[0];
      if (!method) { console.error("Usage: slack.mjs api <method> [json-params]"); process.exit(1); }
      if (RESTRICTED_METHODS[method]) {
        console.error(`ERROR: "${method}" is restricted on Enterprise Grid workspaces.`);
        console.error(`Suggestion: ${RESTRICTED_METHODS[method]}`);
        process.exit(1);
      }
      const params = args[1] ? JSON.parse(args[1]) : {};
      ensureInit();
      const data = runInBrowser(
        `if (!window.__slack) throw new Error("not initialized");
         return await window.__slack.call(args.method, args.params);`,
        { method, params }
      );
      if (!data.ok && data.error === "enterprise_is_restricted") {
        console.error(`ERROR: "${method}" is restricted on this Enterprise Grid workspace.`);
        console.error('Use the "search" command as an alternative.');
        process.exit(1);
      }
      console.log(JSON.stringify(data, null, 2));
      break;
    }

    default:
      console.error(`Slack Browser Tools

Usage: node slack.mjs <command> [args...]

Commands:
  init                              Initialize client, verify auth
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

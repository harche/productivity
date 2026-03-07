#!/usr/bin/env node
// Unified Twitter/X CLI — reads auth from Chrome's cookie store (preferred),
// falls back to Playwright browser injection if Chrome extraction fails.
//
// Usage:
//   node twitter.mjs init
//   node twitter.mjs tweet <tweetId>
//   node twitter.mjs thread <tweetId>
//   node twitter.mjs user <username>
//   node twitter.mjs user-tweets <username> [count]
//   node twitter.mjs search <query> [count]
//   node twitter.mjs timeline [count]
//   node twitter.mjs post <text>
//   node twitter.mjs reply <tweetId> <text>
//   node twitter.mjs like <tweetId>
//   node twitter.mjs retweet <tweetId>
//   node twitter.mjs url <twitterUrl>
//   node twitter.mjs bookmarks [count]
//   node twitter.mjs discover

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { homedir } from "os";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Twitter web app bearer token (constant, same for all users)
const BEARER_TOKEN =
  "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA";

// GraphQL query ID cache
const CACHE_DIR = join(homedir(), ".cache", "twitter-cli");
const QUERY_IDS_FILE = join(CACHE_DIR, "query-ids.json");
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours

// Feature flags used by tweet/timeline operations (captured from browser 2026-03-07)
const TWEET_FEATURES = {
  rweb_video_screen_enabled: false,
  profile_label_improvements_pcf_label_in_post_enabled: true,
  responsive_web_profile_redirect_enabled: false,
  rweb_tipjar_consumption_enabled: false,
  verified_phone_label_enabled: false,
  creator_subscriptions_tweet_preview_api_enabled: true,
  responsive_web_graphql_timeline_navigation_enabled: true,
  responsive_web_graphql_skip_user_profile_image_extensions_enabled: false,
  premium_content_api_read_enabled: false,
  communities_web_enable_tweet_community_results_fetch: true,
  c9s_tweet_anatomy_moderator_badge_enabled: true,
  responsive_web_grok_analyze_button_fetch_trends_enabled: false,
  responsive_web_grok_analyze_post_followups_enabled: true,
  responsive_web_jetfuel_frame: true,
  responsive_web_grok_share_attachment_enabled: true,
  responsive_web_grok_annotations_enabled: true,
  articles_preview_enabled: true,
  responsive_web_edit_tweet_api_enabled: true,
  graphql_is_translatable_rweb_tweet_is_translatable_enabled: true,
  view_counts_everywhere_api_enabled: true,
  longform_notetweets_consumption_enabled: true,
  responsive_web_twitter_article_tweet_consumption_enabled: true,
  tweet_awards_web_tipping_enabled: false,
  content_disclosure_indicator_enabled: true,
  content_disclosure_ai_generated_indicator_enabled: true,
  responsive_web_grok_show_grok_translated_post: false,
  responsive_web_grok_analysis_button_from_backend: true,
  post_ctas_fetch_enabled: true,
  freedom_of_speech_not_reach_fetch_enabled: true,
  standardized_nudges_misinfo: true,
  tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled: true,
  longform_notetweets_rich_text_read_enabled: true,
  longform_notetweets_inline_media_enabled: false,
  responsive_web_grok_image_annotation_enabled: true,
  responsive_web_grok_imagine_annotation_enabled: true,
  responsive_web_grok_community_note_auto_translation_is_enabled: false,
  responsive_web_enhance_cards_enabled: false,
};

// Feature flags used by user profile operations
const USER_FEATURES = {
  hidden_profile_subscriptions_enabled: true,
  profile_label_improvements_pcf_label_in_post_enabled: true,
  responsive_web_profile_redirect_enabled: false,
  rweb_tipjar_consumption_enabled: false,
  verified_phone_label_enabled: false,
  subscriptions_verification_info_is_identity_verified_enabled: true,
  subscriptions_verification_info_verified_since_enabled: true,
  highlights_tweets_tab_ui_enabled: true,
  responsive_web_twitter_article_notes_tab_enabled: true,
  subscriptions_feature_can_gift_premium: true,
  creator_subscriptions_tweet_preview_api_enabled: true,
  responsive_web_graphql_skip_user_profile_image_extensions_enabled: false,
  responsive_web_graphql_timeline_navigation_enabled: true,
};

// --- Backend selection: Chrome (direct) vs Playwright (fallback) ---

let backend = null;
let session = null;

async function ensureBackend() {
  if (backend) return;

  try {
    const mod = await import("./chrome-session.mjs");
    session = mod.getTwitterSession();
    backend = "chrome";
    return;
  } catch (e) {
    // Chrome extraction failed — fall back to Playwright
  }

  const check = spawnSync("which", ["playwright-cli"], { encoding: "utf-8" });
  if (check.status !== 0) {
    throw new Error(
      "Could not extract Twitter session from Chrome, and playwright-cli is not installed.\n" +
        "Either log into X in Chrome, or run: playwright-cli open --extension"
    );
  }

  backend = "playwright";
}

// --- Direct API caller (Chrome backend) ---

let lastCallTime = 0;

async function directTwitterApi(url, options = {}) {
  // Rate limiting — random delay between 800-1500ms
  const now = Date.now();
  const delay = 800 + Math.floor(Math.random() * 700);
  const wait = Math.max(0, delay - (now - lastCallTime));
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastCallTime = Date.now();

  const method = options.method || "GET";
  const headers = {
    Authorization: `Bearer ${BEARER_TOKEN}`,
    "x-csrf-token": session.ct0,
    "x-twitter-active-user": "yes",
    "x-twitter-auth-type": "OAuth2Session",
    "x-twitter-client-language": "en",
    Cookie: `auth_token=${session.authToken}; ct0=${session.ct0}`,
    Origin: "https://x.com",
    Referer: "https://x.com/",
    "User-Agent":
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
  };

  if (method === "POST") {
    headers["Content-Type"] = "application/json";
  }

  const fetchOpts = { method, headers };
  if (options.body) fetchOpts.body = options.body;

  const res = await fetch(url, fetchOpts);

  if (res.status === 429) {
    const resetHeader = res.headers.get("x-rate-limit-reset");
    const waitMs = resetHeader
      ? Math.max(parseInt(resetHeader, 10) * 1000 - Date.now(), 10000)
      : 60000;
    console.error(`Rate limited. Waiting ${Math.ceil(waitMs / 1000)}s...`);
    await new Promise((r) => setTimeout(r, waitMs));
    return directTwitterApi(url, options);
  }

  if (res.status === 401 || res.status === 403) {
    throw new Error(
      `Auth error (${res.status}). Your session may have expired. Re-login to X in Chrome.`
    );
  }

  // Some endpoints (SearchTimeline) return 404 with empty body when
  // x-client-transaction-id is missing — this is Twitter's anti-automation.
  if (res.status === 404) {
    const body = await res.text();
    if (body.length === 0) {
      throw new Error(
        "Request blocked (empty 404). This endpoint requires x-client-transaction-id. " +
          "Use the Playwright backend (playwright-cli open --extension) for this operation."
      );
    }
    return JSON.parse(body);
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
    const ready = await page.evaluate(() => typeof window.__twitter !== "undefined" && !!window.__twitter.ready);
    return JSON.stringify(ready);
  }`;
  const checkProc = spawnSync("playwright-cli", ["run-code", checkCode], {
    encoding: "utf-8",
    timeout: 10000,
  });
  const checkOut = checkProc.stdout || "";
  if (checkOut.includes("true")) return;

  const script = readFileSync(join(__dirname, "twitter-client.js"), "utf-8");
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

function playwrightCall(url, options) {
  return runInBrowser(
    `if (!window.__twitter) throw new Error("not initialized");
     return await window.__twitter.call(args.url, args.options);`,
    { url, options }
  );
}

// Ensure playwright-cli has a browser connected (auto-open via extension if needed).
function ensurePlaywrightBrowser() {
  const check = spawnSync("playwright-cli", ["list"], {
    encoding: "utf-8",
    timeout: 5000,
  });
  if (check.status === 0 && check.stdout.includes("browser-type:")) return;

  console.error("No browser connected. Opening via Playwright extension...");
  const open = spawnSync("playwright-cli", ["open", "--extension"], {
    encoding: "utf-8",
    timeout: 15000,
  });
  if (open.status !== 0) {
    const err = open.stderr || open.stdout || "Unknown error";
    console.error("ERROR: Could not connect to Chrome:", err.trim());
    console.error("Run manually: playwright-cli open --extension");
    process.exit(1);
  }
}

// Navigate the browser to a URL and intercept a specific API response.
// Used for endpoints that require x-client-transaction-id (e.g., SearchTimeline).
function playwrightNavigateAndCapture(pageUrl, apiPattern) {
  const runCode = `async page => {
    const apiPattern = ${JSON.stringify(apiPattern)};
    let captured = null;

    page.on("response", async res => {
      if (!captured && res.url().includes(apiPattern) && res.status() === 200) {
        try { captured = await res.json(); } catch {}
      }
    });

    await page.goto(${JSON.stringify(pageUrl)}, { waitUntil: "domcontentloaded", timeout: 20000 });
    // Wait for the API response
    for (let i = 0; i < 20 && !captured; i++) {
      await page.waitForTimeout(500);
    }

    return JSON.stringify(captured || { error: "API response not captured" });
  }`;

  const proc = spawnSync("playwright-cli", ["run-code", runCode], {
    encoding: "utf-8",
    timeout: 35000,
  });

  if (proc.status !== 0) {
    const err = proc.stderr || proc.stdout || "Unknown error";
    console.error("ERROR:", err.trim());
    process.exit(1);
  }

  const output = proc.stdout;
  const match = output.match(/### Result\n([\s\S]*?)(?:\n###|$)/);
  if (!match) {
    console.error("ERROR: Could not parse playwright-cli output");
    process.exit(1);
  }

  try {
    return JSON.parse(JSON.parse(match[1].trim()));
  } catch {
    try {
      return JSON.parse(match[1].trim());
    } catch {
      return { error: "Failed to parse response" };
    }
  }
}

// --- Unified API interface ---

async function twitterApi(url, options = {}) {
  if (backend === "chrome") {
    return directTwitterApi(url, options);
  }
  ensurePlaywrightInit();
  return playwrightCall(url, options);
}

// --- GraphQL query ID discovery ---

function loadCachedQueryIds() {
  if (!existsSync(QUERY_IDS_FILE)) return null;
  try {
    const data = JSON.parse(readFileSync(QUERY_IDS_FILE, "utf-8"));
    if (Date.now() - data.timestamp < CACHE_TTL) return data.ids;
  } catch {}
  return null;
}

function saveCachedQueryIds(ids) {
  if (!existsSync(CACHE_DIR)) mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(
    QUERY_IDS_FILE,
    JSON.stringify({ ids, timestamp: Date.now() }, null, 2)
  );
}

async function discoverQueryIds() {
  console.error("Discovering GraphQL query IDs from X...");

  const mainRes = await fetch("https://x.com", {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    },
    redirect: "follow",
  });
  const html = await mainRes.text();

  const scriptUrls = new Set();
  for (const m of html.matchAll(
    /(?:src|href)="(https:\/\/abs\.twimg\.com\/responsive-web\/client-web[^"]*\.js)"/g
  )) {
    scriptUrls.add(m[1]);
  }

  if (scriptUrls.size === 0) {
    throw new Error(
      "Could not find Twitter JS bundles. The page structure may have changed."
    );
  }

  const ids = {};
  let fetched = 0;

  for (const url of scriptUrls) {
    try {
      const jsRes = await fetch(url);
      const js = await jsRes.text();

      for (const match of js.matchAll(
        /queryId:\s*"([^"]+)",\s*operationName:\s*"([^"]+)"/g
      )) {
        ids[match[2]] = match[1];
      }

      fetched++;
    } catch {}
  }

  if (Object.keys(ids).length === 0) {
    throw new Error(
      `Fetched ${fetched}/${scriptUrls.size} bundles but found no query IDs. Extraction pattern may need updating.`
    );
  }

  saveCachedQueryIds(ids);
  console.error(
    `Discovered ${Object.keys(ids).length} operations from ${fetched} bundles.`
  );
  return ids;
}

let queryIds = null;

async function getQueryIds() {
  if (queryIds) return queryIds;
  queryIds = loadCachedQueryIds();
  if (queryIds) return queryIds;
  queryIds = await discoverQueryIds();
  return queryIds;
}

async function getQueryId(operationName) {
  const ids = await getQueryIds();
  const id = ids[operationName];
  if (!id) {
    queryIds = await discoverQueryIds();
    const retryId = queryIds[operationName];
    if (!retryId) {
      throw new Error(
        `Unknown GraphQL operation: ${operationName}. Run 'discover' to refresh query IDs.`
      );
    }
    return retryId;
  }
  return id;
}

// --- GraphQL helpers ---

async function graphqlGet(operationName, variables, features, fieldToggles) {
  const queryId = await getQueryId(operationName);
  const params = new URLSearchParams();
  params.set("variables", JSON.stringify(variables));
  params.set("features", JSON.stringify(features));
  if (fieldToggles) params.set("fieldToggles", JSON.stringify(fieldToggles));
  const url = `https://x.com/i/api/graphql/${queryId}/${operationName}?${params}`;
  return twitterApi(url);
}

async function graphqlPost(operationName, variables, features) {
  const queryId = await getQueryId(operationName);
  const url = `https://x.com/i/api/graphql/${queryId}/${operationName}`;
  const body = { variables };
  if (features) body.features = features;
  return twitterApi(url, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// --- Search via JS injection (generates x-client-transaction-id in-browser) ---

function searchViaJsInjection(query, count) {
  ensurePlaywrightBrowser();

  const runCode = `async page => {
    const args = ${JSON.stringify({ query, count })};

    // Ensure we're on x.com so webpack modules are available
    const url = await page.url();
    if (!url.includes('x.com') && !url.includes('twitter.com')) {
      await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 20000 });
    }

    // Wait for webpack chunks and module cache to be fully loaded
    for (let i = 0; i < 20; i++) {
      const ready = await page.evaluate(() => {
        const chunks = window.webpackChunk_twitter_responsive_web;
        if (!chunks || !chunks.length) return false;
        let req = null;
        chunks.push([['__ready_check_' + Date.now() + '__'], {}, (r) => { req = r; }]);
        return !!(req && req.c && Object.keys(req.c).length > 100);
      });
      if (ready) break;
      await page.waitForTimeout(500);
    }

    const result = await page.evaluate(async ({ query, count }) => {
      // Access webpack require via chunk push trick
      const chunks = window.webpackChunk_twitter_responsive_web;
      if (!chunks) return { error: 'Not on x.com or webpack chunks not available' };

      // Get webpack require with retry (cache may not be populated on first push)
      let webpackRequire = null;
      for (let attempt = 0; attempt < 5; attempt++) {
        chunks.push([['__search_probe_' + Date.now()], {}, (req) => { webpackRequire = req; }]);
        if (webpackRequire && webpackRequire.c && Object.keys(webpackRequire.c).length > 0) break;
        webpackRequire = null;
        await new Promise(r => setTimeout(r, 500));
      }
      if (!webpackRequire || !webpackRequire.c) return { error: 'Could not access webpack module cache' };

      // Find the transaction ID generator module (exports.jJ = async function(host, path, method))
      let generateTxId = null;
      for (const id of Object.keys(webpackRequire.c)) {
        const mod = webpackRequire.c[id];
        if (!mod?.exports?.jJ || !mod?.exports?.ZP) continue;
        const fn = mod.exports.ZP.toString();
        if (fn.includes('x-client-transaction-id')) {
          generateTxId = mod.exports.jJ;
          break;
        }
      }
      if (!generateTxId) return { error: 'Transaction ID generator not found in webpack modules' };

      // Find SearchTimeline query ID from chunk module factories
      let searchQueryId = null;
      for (const chunk of chunks) {
        if (!chunk[1]) continue;
        for (const [, factory] of Object.entries(chunk[1])) {
          if (typeof factory !== 'function') continue;
          const src = factory.toString();
          const match = src.match(/queryId:\s*"([^"]+)",\s*operationName:\s*"SearchTimeline",\s*operationType:\s*"query"/);
          if (match) { searchQueryId = match[1]; break; }
        }
        if (searchQueryId) break;
      }
      if (!searchQueryId) return { error: 'SearchTimeline queryId not found in webpack chunks' };

      // Get CSRF token
      const ct0 = document.cookie.split(';').map(c => c.trim())
        .find(c => c.startsWith('ct0='))?.split('=')[1];
      if (!ct0) return { error: 'No CSRF token found in cookies' };

      // Build request
      const variables = {
        rawQuery: query, count, querySource: 'typed_query',
        product: 'Latest', withGrokTranslatedBio: false,
      };
      const features = ${JSON.stringify(TWEET_FEATURES)};
      const params = new URLSearchParams();
      params.set('variables', JSON.stringify(variables));
      params.set('features', JSON.stringify(features));

      const apiPath = '/i/api/graphql/' + searchQueryId + '/SearchTimeline';
      const fullUrl = 'https://x.com' + apiPath + '?' + params.toString();
      const txId = await generateTxId('x.com', apiPath, 'GET');

      const response = await fetch(fullUrl, {
        method: 'GET',
        headers: {
          'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
          'x-csrf-token': ct0,
          'x-twitter-auth-type': 'OAuth2Session',
          'x-twitter-active-user': 'yes',
          'x-twitter-client-language': 'en',
          'x-client-transaction-id': txId,
        },
        credentials: 'include',
      });

      if (response.status !== 200) {
        const body = await response.text();
        return { error: 'API returned status ' + response.status, body: body.substring(0, 500) };
      }

      return await response.json();
    }, args);

    return JSON.stringify(result);
  }`;

  const proc = spawnSync("playwright-cli", ["run-code", runCode], {
    encoding: "utf-8",
    timeout: 60000,
  });

  if (proc.status !== 0) {
    return { error: "Playwright process failed: " + (proc.stderr || proc.stdout || "unknown").substring(0, 200) };
  }

  const output = proc.stdout;

  // Handle error responses from playwright-cli
  if (output.includes("### Error")) {
    const errMatch = output.match(/### Error\n([\s\S]*?)(?:\n###|$)/);
    return { error: "Playwright error: " + (errMatch ? errMatch[1].trim().substring(0, 200) : "unknown") };
  }

  const match = output.match(/### Result\n([\s\S]*?)(?:\n###|$)/);
  if (!match) {
    return { error: "Could not parse playwright-cli output" };
  }

  try {
    return JSON.parse(JSON.parse(match[1].trim()));
  } catch {
    try {
      return JSON.parse(match[1].trim());
    } catch {
      return { error: "Failed to parse response" };
    }
  }
}

// Legacy fallback: navigate the browser to search URL and intercept the response.
function searchViaPlaywrightNavigation(query, count) {
  ensurePlaywrightBrowser();
  const encodedQuery = encodeURIComponent(query);
  const pageUrl = `https://x.com/search?q=${encodedQuery}&f=live`;
  const data = playwrightNavigateAndCapture(pageUrl, "SearchTimeline");
  if (data.error) {
    console.error("Search failed:", data.error);
    process.exit(1);
  }
  return data;
}

// --- URL parser ---

function parseTwitterUrl(url) {
  const parsed = new URL(url);

  const tweetMatch = parsed.pathname.match(/\/([^/]+)\/status\/(\d+)/);
  if (tweetMatch) {
    return { type: "tweet", username: tweetMatch[1], tweetId: tweetMatch[2] };
  }

  if (parsed.pathname === "/search" || parsed.pathname.startsWith("/search")) {
    return {
      type: "search",
      query: parsed.searchParams.get("q") || "",
    };
  }

  if (parsed.pathname === "/i/bookmarks") {
    return { type: "bookmarks" };
  }

  if (parsed.pathname === "/home") {
    return { type: "timeline" };
  }

  const userMatch = parsed.pathname.match(/^\/([a-zA-Z0-9_]+)\/?$/);
  if (
    userMatch &&
    ![
      "home",
      "explore",
      "notifications",
      "messages",
      "settings",
      "i",
    ].includes(userMatch[1])
  ) {
    return { type: "user", username: userMatch[1] };
  }

  return { type: "unknown", url };
}

// --- Response formatters ---

function formatTweet(result) {
  if (!result) return null;

  if (result.__typename === "TweetWithVisibilityResults") {
    result = result.tweet;
  }

  if (!result || !result.legacy) return null;

  const legacy = result.legacy;
  const userResult = result.core?.user_results?.result;
  // Twitter moved screen_name/name from legacy to core sub-object
  const userCore = userResult?.core;
  const userLegacy = userResult?.legacy;

  let text = legacy.full_text || legacy.text || "";
  if (legacy.entities?.urls) {
    for (const u of legacy.entities.urls) {
      text = text.replace(u.url, u.expanded_url || u.display_url || u.url);
    }
  }
  if (legacy.entities?.media) {
    for (const m of legacy.entities.media) {
      text = text.replace(m.url, "").trim();
    }
  }

  const tweet = {
    id: legacy.id_str || result.rest_id,
    text,
    author: userCore
      ? { handle: userCore.screen_name, name: userCore.name }
      : userLegacy
        ? { handle: userLegacy.screen_name, name: userLegacy.name }
        : undefined,
    created_at: legacy.created_at,
    metrics: {
      likes: legacy.favorite_count,
      retweets: legacy.retweet_count,
      replies: legacy.reply_count,
      quotes: legacy.quote_count,
      views: result.views?.count ? parseInt(result.views.count) : undefined,
    },
  };

  if (legacy.in_reply_to_status_id_str) {
    tweet.in_reply_to = legacy.in_reply_to_status_id_str;
    tweet.in_reply_to_user = legacy.in_reply_to_screen_name;
  }

  if (result.quoted_status_result?.result) {
    const qt = formatTweet(result.quoted_status_result.result);
    if (qt) tweet.quoted_tweet = qt;
  }

  const media = legacy.extended_entities?.media || legacy.entities?.media;
  if (media && media.length > 0) {
    tweet.media = media.map((m) => ({
      type: m.type,
      url: m.media_url_https || m.url,
    }));
  }

  return tweet;
}

function formatUser(result) {
  if (!result) return null;
  const legacy = result.legacy || {};
  // Twitter moved screen_name/name/created_at to core sub-object
  const core = result.core || {};

  return {
    id: result.rest_id,
    handle: core.screen_name || legacy.screen_name,
    name: core.name || legacy.name,
    description: legacy.description || result.profile_bio?.description,
    location: result.location?.location || legacy.location || undefined,
    url:
      legacy.entities?.url?.urls?.[0]?.expanded_url ||
      legacy.url ||
      undefined,
    verified: legacy.verified || result.is_blue_verified || false,
    followers: legacy.followers_count,
    following: legacy.friends_count,
    tweets: legacy.statuses_count,
    created_at: core.created_at || legacy.created_at,
  };
}

function extractTimelineTweets(data) {
  const tweets = [];

  function extractFromInstructions(instructions) {
    for (const instruction of instructions || []) {
      const entries = instruction.entries;
      if (!entries) continue;

      for (const entry of entries) {
        const content = entry.content;
        if (!content) continue;

        if (content.itemContent?.tweet_results?.result) {
          const tweet = formatTweet(content.itemContent.tweet_results.result);
          if (tweet) tweets.push(tweet);
          continue;
        }

        if (content.items) {
          for (const item of content.items) {
            if (item.item?.itemContent?.tweet_results?.result) {
              const tweet = formatTweet(
                item.item.itemContent.tweet_results.result
              );
              if (tweet) tweets.push(tweet);
            }
          }
        }
      }
    }
  }

  // Navigate known response shapes
  if (data?.data?.home?.home_timeline_urt?.instructions) {
    extractFromInstructions(data.data.home.home_timeline_urt.instructions);
  } else if (data?.data?.user?.result?.timeline?.timeline?.instructions) {
    extractFromInstructions(
      data.data.user.result.timeline.timeline.instructions
    );
  } else if (
    data?.data?.search_by_raw_query?.search_timeline?.timeline?.instructions
  ) {
    extractFromInstructions(
      data.data.search_by_raw_query.search_timeline.timeline.instructions
    );
  } else if (data?.data?.bookmark_timeline_v2?.timeline?.instructions) {
    extractFromInstructions(
      data.data.bookmark_timeline_v2.timeline.instructions
    );
  } else if (
    data?.data?.threaded_conversation_with_injections_v2?.instructions
  ) {
    extractFromInstructions(
      data.data.threaded_conversation_with_injections_v2.instructions
    );
  }

  return tweets;
}

// --- Commands ---

const [, , command, ...args] = process.argv;

async function main() {
  await ensureBackend();

  switch (command) {
    case "init": {
      // Use badge_count as auth check (verify_credentials is gone)
      const data = await twitterApi(
        "https://x.com/i/api/2/badge_count/badge_count.json?supports_ntab_urt=1"
      );
      if (data.errors) {
        console.error("Auth failed:", JSON.stringify(data.errors));
        process.exit(1);
      }
      console.log(
        JSON.stringify(
          {
            ok: true,
            notifications: data.ntab_unread_count,
            dms: data.dm_unread_count,
            backend,
          },
          null,
          2
        )
      );
      break;
    }

    case "tweet": {
      const tweetId = args[0];
      if (!tweetId) {
        console.error("Usage: twitter.mjs tweet <tweetId>");
        process.exit(1);
      }
      const data = await graphqlGet(
        "TweetResultByRestId",
        {
          tweetId,
          withCommunity: false,
          includePromotedContent: false,
          withVoice: false,
        },
        TWEET_FEATURES,
        { withArticlePlainText: false }
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweet = formatTweet(data.data?.tweetResult?.result);
      if (!tweet) {
        console.error("Tweet not found or unavailable.");
        process.exit(1);
      }
      console.log(JSON.stringify(tweet, null, 2));
      break;
    }

    case "thread": {
      const tweetId = args[0];
      if (!tweetId) {
        console.error("Usage: twitter.mjs thread <tweetId>");
        process.exit(1);
      }
      const data = await graphqlGet(
        "TweetDetail",
        {
          focalTweetId: tweetId,
          with_rux_injections: false,
          rankingMode: "Relevance",
          includePromotedContent: false,
          withCommunity: true,
          withQuickPromoteEligibilityTweetFields: true,
          withBirdwatchNotes: true,
          withVoice: true,
        },
        TWEET_FEATURES,
        { withArticlePlainText: false }
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweets = extractTimelineTweets(data);
      console.log(JSON.stringify(tweets, null, 2));
      break;
    }

    case "user": {
      const username = args[0]?.replace(/^@/, "");
      if (!username) {
        console.error("Usage: twitter.mjs user <username>");
        process.exit(1);
      }
      const data = await graphqlGet(
        "UserByScreenName",
        {
          screen_name: username,
          withGrokTranslatedBio: false,
        },
        USER_FEATURES,
        { withPayments: false, withAuxiliaryUserLabels: true }
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const user = formatUser(data.data?.user?.result);
      if (!user) {
        console.error("User not found.");
        process.exit(1);
      }
      console.log(JSON.stringify(user, null, 2));
      break;
    }

    case "user-tweets": {
      const username = args[0]?.replace(/^@/, "");
      const count = parseInt(args[1]) || 20;
      if (!username) {
        console.error("Usage: twitter.mjs user-tweets <username> [count]");
        process.exit(1);
      }

      // First get the user's ID
      const userData = await graphqlGet(
        "UserByScreenName",
        {
          screen_name: username,
          withGrokTranslatedBio: false,
        },
        USER_FEATURES,
        { withPayments: false, withAuxiliaryUserLabels: true }
      );
      const userId = userData.data?.user?.result?.rest_id;
      if (!userId) {
        console.error("User not found:", username);
        process.exit(1);
      }

      const data = await graphqlGet(
        "UserTweets",
        {
          userId,
          count,
          includePromotedContent: false,
          withQuickPromoteEligibilityTweetFields: true,
          withVoice: true,
        },
        TWEET_FEATURES,
        { withArticlePlainText: false }
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweets = extractTimelineTweets(data);
      console.log(
        JSON.stringify(
          { user: username, count: tweets.length, tweets },
          null,
          2
        )
      );
      break;
    }

    case "search": {
      const query = args[0];
      const count = parseInt(args[1]) || 20;
      if (!query) {
        console.error("Usage: twitter.mjs search <query> [count]");
        process.exit(1);
      }

      // Try JS injection first (fastest, no browser navigation needed)
      let data = searchViaJsInjection(query, count);
      if (data.error) {
        // Fall back to navigation-based search
        console.error(
          "JS injection search failed:", data.error, "— falling back to navigation..."
        );
        data = searchViaPlaywrightNavigation(query, count);
      }

      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweets = extractTimelineTweets(data);
      console.log(
        JSON.stringify(
          { query, count: tweets.length, tweets },
          null,
          2
        )
      );
      break;
    }

    case "timeline": {
      const count = parseInt(args[0]) || 20;
      const data = await graphqlGet(
        "HomeTimeline",
        {
          count,
          includePromotedContent: false,
          latestControlAvailable: true,
          requestContext: "launch",
          withCommunity: true,
          seenTweetIds: [],
        },
        TWEET_FEATURES,
        { withArticlePlainText: false }
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweets = extractTimelineTweets(data);
      console.log(
        JSON.stringify({ count: tweets.length, tweets }, null, 2)
      );
      break;
    }

    case "post": {
      const text = args[0];
      if (!text) {
        console.error("Usage: twitter.mjs post <text>");
        process.exit(1);
      }
      const data = await graphqlPost(
        "CreateTweet",
        {
          tweet_text: text,
          dark_request: false,
          media: {
            media_entities: [],
            possibly_sensitive: false,
          },
          semantic_annotation_ids: [],
        },
        TWEET_FEATURES
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweet = formatTweet(
        data.data?.create_tweet?.tweet_results?.result
      );
      console.log(
        JSON.stringify(
          { ok: true, tweet: tweet || { id: "created" } },
          null,
          2
        )
      );
      break;
    }

    case "reply": {
      const tweetId = args[0];
      const text = args[1];
      if (!tweetId || !text) {
        console.error("Usage: twitter.mjs reply <tweetId> <text>");
        process.exit(1);
      }
      const data = await graphqlPost(
        "CreateTweet",
        {
          tweet_text: text,
          reply: {
            in_reply_to_tweet_id: tweetId,
            exclude_reply_user_ids: [],
          },
          dark_request: false,
          media: {
            media_entities: [],
            possibly_sensitive: false,
          },
          semantic_annotation_ids: [],
        },
        TWEET_FEATURES
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweet = formatTweet(
        data.data?.create_tweet?.tweet_results?.result
      );
      console.log(
        JSON.stringify(
          {
            ok: true,
            in_reply_to: tweetId,
            tweet: tweet || { id: "created" },
          },
          null,
          2
        )
      );
      break;
    }

    case "like": {
      const tweetId = args[0];
      if (!tweetId) {
        console.error("Usage: twitter.mjs like <tweetId>");
        process.exit(1);
      }
      const data = await graphqlPost("FavoriteTweet", {
        tweet_id: tweetId,
      });
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      console.log(JSON.stringify({ ok: true, liked: tweetId }, null, 2));
      break;
    }

    case "retweet": {
      const tweetId = args[0];
      if (!tweetId) {
        console.error("Usage: twitter.mjs retweet <tweetId>");
        process.exit(1);
      }
      const data = await graphqlPost("CreateRetweet", {
        tweet_id: tweetId,
        dark_request: false,
      });
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      console.log(
        JSON.stringify({ ok: true, retweeted: tweetId }, null, 2)
      );
      break;
    }

    case "bookmarks": {
      const count = parseInt(args[0]) || 20;
      const data = await graphqlGet(
        "Bookmarks",
        {
          count,
          includePromotedContent: false,
        },
        TWEET_FEATURES
      );
      if (data.errors) {
        console.error("API error:", JSON.stringify(data.errors));
        process.exit(1);
      }
      const tweets = extractTimelineTweets(data);
      console.log(
        JSON.stringify({ count: tweets.length, tweets }, null, 2)
      );
      break;
    }

    case "url": {
      const url = args[0];
      if (!url) {
        console.error("Usage: twitter.mjs url <twitterUrl>");
        process.exit(1);
      }
      const parsed = parseTwitterUrl(url);

      switch (parsed.type) {
        case "tweet": {
          const data = await graphqlGet(
            "TweetDetail",
            {
              focalTweetId: parsed.tweetId,
              with_rux_injections: false,
              rankingMode: "Relevance",
              includePromotedContent: false,
              withCommunity: true,
              withQuickPromoteEligibilityTweetFields: true,
              withBirdwatchNotes: true,
              withVoice: true,
            },
            TWEET_FEATURES,
            { withArticlePlainText: false }
          );
          if (data.errors) {
            console.error("API error:", JSON.stringify(data.errors));
            process.exit(1);
          }
          const tweets = extractTimelineTweets(data);
          console.log(
            JSON.stringify(
              { type: "tweet_thread", user: parsed.username, tweets },
              null,
              2
            )
          );
          break;
        }
        case "user": {
          const data = await graphqlGet(
            "UserByScreenName",
            {
              screen_name: parsed.username,
              withGrokTranslatedBio: false,
            },
            USER_FEATURES,
            { withPayments: false, withAuxiliaryUserLabels: true }
          );
          const user = formatUser(data.data?.user?.result);
          console.log(
            JSON.stringify({ type: "user_profile", user }, null, 2)
          );
          break;
        }
        case "search": {
          let data = searchViaJsInjection(parsed.query, 20);
          if (data.error) {
            console.error(
              "JS injection search failed:", data.error, "— falling back to navigation..."
            );
            data = searchViaPlaywrightNavigation(parsed.query, 20);
          }
          const tweets = extractTimelineTweets(data);
          console.log(
            JSON.stringify(
              { type: "search", query: parsed.query, tweets },
              null,
              2
            )
          );
          break;
        }
        case "bookmarks": {
          const data = await graphqlGet(
            "Bookmarks",
            { count: 20, includePromotedContent: false },
            TWEET_FEATURES
          );
          const tweets = extractTimelineTweets(data);
          console.log(
            JSON.stringify({ type: "bookmarks", tweets }, null, 2)
          );
          break;
        }
        case "timeline": {
          const data = await graphqlGet(
            "HomeTimeline",
            {
              count: 20,
              includePromotedContent: false,
              latestControlAvailable: true,
              requestContext: "launch",
              withCommunity: true,
              seenTweetIds: [],
            },
            TWEET_FEATURES,
            { withArticlePlainText: false }
          );
          const tweets = extractTimelineTweets(data);
          console.log(
            JSON.stringify({ type: "timeline", tweets }, null, 2)
          );
          break;
        }
        default:
          console.error("Could not parse URL:", url);
          process.exit(1);
      }
      break;
    }

    case "discover": {
      queryIds = null;
      const ids = await discoverQueryIds();
      const operations = Object.keys(ids).sort();
      console.log(
        JSON.stringify(
          {
            ok: true,
            count: operations.length,
            cached_at: QUERY_IDS_FILE,
            operations: operations.slice(0, 50),
          },
          null,
          2
        )
      );
      break;
    }

    default:
      console.error(`Twitter/X CLI

Usage: node twitter.mjs <command> [args...]

Commands:
  init                              Verify auth, show current user
  url <twitterUrl>                  Parse URL and fetch content
  tweet <tweetId>                   Get a single tweet
  thread <tweetId>                  Get tweet with conversation
  user <username>                   Get user profile
  user-tweets <username> [count]    Get user's tweets
  search <query> [count]            Search tweets
  timeline [count]                  Home timeline
  post <text>                       Post a tweet
  reply <tweetId> <text>            Reply to a tweet
  like <tweetId>                    Like a tweet
  retweet <tweetId>                 Retweet
  bookmarks [count]                 List bookmarks
  discover                          Refresh GraphQL query IDs`);
      process.exit(command ? 1 : 0);
  }
}

main().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});

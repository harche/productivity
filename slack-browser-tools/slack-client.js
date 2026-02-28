// Slack Browser Client — Injectable script for Playwright CLI
// Injects window.__slack with token extraction, rate-limited API caller, and helpers.
// Usage: playwright-cli run-code 'async page => { ... page.evaluate(script) ... }'

(async () => {
  if (window.__slack && window.__slack.token) {
    // Already initialized — verify token still works
    try {
      var check = await window.__slack.auth();
      if (check.ok) return { initialized: true, cached: true, user: check.user, team: check.team };
    } catch (_) {
      // Token stale, re-initialize below
    }
  }

  // --- Token Extraction ---
  var token = null;

  // Detect current workspace from URL
  var teamIdMatch = window.location.pathname.match(/\/client\/([A-Z0-9]+)\//);
  var currentTeamId = teamIdMatch ? teamIdMatch[1] : null;

  // Method 1: Read from localConfig_v2 → teams → {teamId} → token (instant, workspace-aware)
  try {
    var configRaw = localStorage.getItem("localConfig_v2");
    if (configRaw) {
      var config = JSON.parse(configRaw);
      var teams = config.teams || {};

      // If we know the current workspace, get its token directly
      if (currentTeamId && teams[currentTeamId] && teams[currentTeamId].token) {
        token = teams[currentTeamId].token;
      }

      // Otherwise, try each team until we find a valid token
      if (!token) {
        var teamIds = Object.keys(teams);
        for (var i = 0; i < teamIds.length; i++) {
          if (teams[teamIds[i]].token) {
            token = teams[teamIds[i]].token;
            break;
          }
        }
      }
    }
  } catch (_) {}

  // Method 2: Fallback to XHR + fetch interception if localStorage didn't have it
  if (!token) {
    token = await new Promise(function (resolve, reject) {
      var origSend = XMLHttpRequest.prototype.send;
      var origFetch = window.fetch;
      var timer = setTimeout(function () { restore(); reject(new Error("Token extraction timed out. Try clicking around in Slack, then retry.")); }, 15000);

      function restore() {
        XMLHttpRequest.prototype.send = origSend;
        window.fetch = origFetch;
      }

      function found(t) {
        restore();
        clearTimeout(timer);
        resolve(t);
      }

      // Intercept fetch
      window.fetch = function () {
        var args = arguments;
        try {
          var opts = args[1] || {};
          var body = opts.body;
          if (body && typeof body === "string") {
            var m = body.match(/token=(xoxc-[^&]+)/);
            if (m) { found(m[1]); return origFetch.apply(this, args); }
          }
          if (body instanceof URLSearchParams) {
            var t = body.get("token");
            if (t && t.startsWith("xoxc-")) { found(t); return origFetch.apply(this, args); }
          }
          if (body instanceof FormData) {
            var t2 = body.get("token");
            if (t2 && typeof t2 === "string" && t2.startsWith("xoxc-")) { found(t2); return origFetch.apply(this, args); }
          }
        } catch (_) {}
        return origFetch.apply(this, args);
      };

      // Intercept XHR
      XMLHttpRequest.prototype.send = function (body) {
        try {
          if (body instanceof FormData) {
            var t = body.get("token");
            if (t && typeof t === "string" && t.startsWith("xoxc-")) found(t);
          }
          if (typeof body === "string" && body.includes("xoxc-")) {
            var m = body.match(/token=(xoxc-[^&]+)/);
            if (m) found(m[1]);
          }
        } catch (_) {}
        return origSend.call(this, body);
      };
    });
  }

  if (!token) throw new Error("Could not extract Slack token.");

  // --- Rate Limiter ---
  // Random delay between 800ms-1500ms to mimic human browsing patterns
  var lastCallTime = 0;
  var MIN_DELAY_MS = 800;
  var MAX_DELAY_MS = 1500;

  function randomDelay() {
    return MIN_DELAY_MS + Math.floor(Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS));
  }

  // --- Core API Caller ---
  async function call(method, params) {
    if (!params) params = {};

    // Rate limiting — enforce randomized delay between calls
    var now = Date.now();
    var target = randomDelay();
    var wait = Math.max(0, target - (now - lastCallTime));
    if (wait > 0) await new Promise(function (r) { setTimeout(r, wait); });
    lastCallTime = Date.now();

    var body = new URLSearchParams();
    body.set("token", token);
    var entries = Object.entries(params);
    for (var i = 0; i < entries.length; i++) {
      if (entries[i][1] !== undefined && entries[i][1] !== null) body.set(entries[i][0], String(entries[i][1]));
    }

    var res = await fetch("/api/" + method, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString()
    });

    // Handle rate limiting — back off and retry
    if (res.status === 429) {
      var retryAfter = parseInt(res.headers.get("Retry-After") || "10", 10);
      await new Promise(function (r) { setTimeout(r, retryAfter * 1000); });
      return call(method, params);
    }

    return await res.json();
  }

  // --- Paginated API Caller ---
  async function callPaginated(method, params, maxPages) {
    if (!maxPages) maxPages = 5;
    var allItems = [];
    var cursor = undefined;
    var pages = 0;

    do {
      var p = Object.assign({}, params);
      if (cursor) p.cursor = cursor;
      var result = await call(method, p);

      if (!result.ok) return result;

      // Collect items from known response keys
      var keys = ["channels", "members", "messages", "users", "matches", "items"];
      for (var i = 0; i < keys.length; i++) {
        if (result[keys[i]]) {
          var items = Array.isArray(result[keys[i]]) ? result[keys[i]] : result[keys[i]].matches || [];
          allItems.push.apply(allItems, items);
        }
      }

      cursor = result.response_metadata && result.response_metadata.next_cursor;
      if (cursor === "") cursor = undefined;
      pages++;

      // Extra random delay between pages to be gentle
      if (cursor && pages < maxPages) {
        var pageDelay = 300 + Math.floor(Math.random() * 700);
        await new Promise(function (r) { setTimeout(r, pageDelay); });
      }
    } while (cursor && pages < maxPages);

    return { ok: true, items: allItems, count: allItems.length, pages: pages };
  }

  // --- Helper Methods ---
  window.__slack = {
    token: token,
    call: call,
    callPaginated: callPaginated,

    auth: function () {
      return call("auth.test");
    },

    channels: function (types) {
      return callPaginated("conversations.list", {
        types: types || "public_channel,private_channel",
        exclude_archived: true,
        limit: 200
      });
    },

    history: function (channelId, limit) {
      return call("conversations.history", {
        channel: channelId,
        limit: limit || 20
      });
    },

    send: function (channelId, text, threadTs) {
      var params = { channel: channelId, text: text };
      if (threadTs) params.thread_ts = threadTs;
      return call("chat.postMessage", params);
    },

    search: function (query, count) {
      return call("search.messages", {
        query: query,
        count: count || 20,
        sort: "timestamp",
        sort_dir: "desc"
      });
    },

    users: function (limit) {
      return callPaginated("users.list", {
        limit: limit || 200
      });
    },

    userInfo: function (userId) {
      return call("users.info", { user: userId });
    },

    thread: function (channelId, threadTs, limit) {
      return call("conversations.replies", {
        channel: channelId,
        ts: threadTs,
        limit: limit || 100
      });
    },

    react: function (channelId, timestamp, emoji) {
      return call("reactions.add", {
        channel: channelId,
        timestamp: timestamp,
        name: emoji
      });
    },

    channelInfo: function (channelId) {
      return call("conversations.info", { channel: channelId });
    }
  };

  // --- Verify ---
  var authResult = await call("auth.test");
  if (!authResult.ok) {
    throw new Error("Auth failed: " + (authResult.error || "unknown"));
  }

  return {
    initialized: true,
    user: authResult.user,
    team: authResult.team,
    user_id: authResult.user_id,
    team_id: authResult.team_id
  };
})()

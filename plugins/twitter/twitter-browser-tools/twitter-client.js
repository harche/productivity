// Twitter/X Browser Client — Injectable script for Playwright CLI
// Injects window.__twitter with auth extraction, rate-limited API caller, and helpers.
// Usage: playwright-cli run-code 'async page => { ... page.evaluate(script) ... }'

(async () => {
  if (window.__twitter && window.__twitter.ready) {
    return { initialized: true, cached: true };
  }

  // --- Auth Extraction ---
  var ct0Match = document.cookie.match(/ct0=([^;]+)/);
  if (!ct0Match) throw new Error("Not logged into Twitter/X. No ct0 cookie found.");
  var csrfToken = ct0Match[1];

  // Twitter web app bearer token (constant, identifies the web client)
  var BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA";

  // --- Rate Limiter ---
  // Random delay between 800ms-1500ms to mimic human browsing patterns
  var lastCallTime = 0;
  var MIN_DELAY_MS = 800;
  var MAX_DELAY_MS = 1500;

  function randomDelay() {
    return MIN_DELAY_MS + Math.floor(Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS));
  }

  // --- Core API Caller ---
  async function call(url, options) {
    if (!options) options = {};

    // Rate limiting — enforce randomized delay between calls
    var now = Date.now();
    var target = randomDelay();
    var wait = Math.max(0, target - (now - lastCallTime));
    if (wait > 0) await new Promise(function (r) { setTimeout(r, wait); });
    lastCallTime = Date.now();

    var method = options.method || "GET";
    var headers = {
      "authorization": "Bearer " + BEARER,
      "x-csrf-token": csrfToken,
      "x-twitter-active-user": "yes",
      "x-twitter-auth-type": "OAuth2Session"
    };

    if (method === "POST") {
      headers["content-type"] = "application/json";
    }

    var fetchOpts = {
      method: method,
      headers: headers,
      credentials: "include"
    };

    if (options.body) {
      fetchOpts.body = typeof options.body === "string" ? options.body : JSON.stringify(options.body);
    }

    var res = await fetch(url, fetchOpts);

    // Handle rate limiting — back off and retry
    if (res.status === 429) {
      var resetHeader = res.headers.get("x-rate-limit-reset");
      var waitTime = resetHeader ? Math.max((parseInt(resetHeader, 10) * 1000) - Date.now(), 10000) : 60000;
      await new Promise(function (r) { setTimeout(r, waitTime); });
      return call(url, options);
    }

    return await res.json();
  }

  // --- GraphQL helpers ---
  async function graphqlGet(endpoint, variables, features) {
    var params = new URLSearchParams();
    params.set("variables", JSON.stringify(variables));
    if (features) params.set("features", JSON.stringify(features));
    return call(endpoint + "?" + params.toString());
  }

  async function graphqlPost(endpoint, variables, features) {
    var body = { variables: variables };
    if (features) body.features = features;
    return call(endpoint, { method: "POST", body: body });
  }

  window.__twitter = {
    ready: true,
    csrfToken: csrfToken,
    call: call,
    graphqlGet: graphqlGet,
    graphqlPost: graphqlPost
  };

  return { initialized: true };
})()

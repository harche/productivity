#!/usr/bin/env node
// YouTube CLI — fetch transcripts, metadata, comments, search, and download.
//
// Usage:
//   node youtube.mjs url <youtubeUrl>
//   node youtube.mjs video <videoId>
//   node youtube.mjs transcript <videoId> [--lang <code>] [--timestamps]
//   node youtube.mjs comments <videoId> [count]
//   node youtube.mjs search <query> [count]
//   node youtube.mjs channel <handle>
//   node youtube.mjs channel-videos <handle> [count]
//   node youtube.mjs playlist <playlistId>

import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── Helpers ──────────────────────────────────────────────────────────────────

function out(data) {
  console.log(JSON.stringify(data, null, 2));
}

function fail(msg) {
  console.error(JSON.stringify({ error: msg }));
  process.exit(1);
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith("--")) {
      const key = argv[i].slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith("--")) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    } else {
      args._.push(argv[i]);
    }
  }
  return args;
}

// Extract video ID from various YouTube URL formats
function extractVideoId(input) {
  if (/^[a-zA-Z0-9_-]{11}$/.test(input)) return input;

  const patterns = [
    /(?:youtube\.com\/watch\?.*v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/|youtube\.com\/live\/)([a-zA-Z0-9_-]{11})/,
  ];
  for (const p of patterns) {
    const m = input.match(p);
    if (m) return m[1];
  }
  return null;
}

// Extract playlist ID from URL
function extractPlaylistId(input) {
  const m = input.match(/[?&]list=([a-zA-Z0-9_-]+)/);
  return m ? m[1] : input;
}

// Extract channel handle from URL
function extractChannelHandle(input) {
  const m = input.match(/youtube\.com\/@([a-zA-Z0-9_.-]+)/);
  return m ? m[1] : input.replace(/^@/, "");
}

// ─── YouTube Innertube API ───────────────────────────────────────────────────

const INNERTUBE_API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8";
const INNERTUBE_CLIENT = {
  clientName: "WEB",
  clientVersion: "2.20240101.00.00",
  hl: "en",
  gl: "US",
};
// ANDROID client is required for caption URLs that actually work
const INNERTUBE_CLIENT_ANDROID = {
  clientName: "ANDROID",
  clientVersion: "20.10.38",
};

async function innertubePost(endpoint, body) {
  const url = `https://www.youtube.com/youtubei/v1/${endpoint}?key=${INNERTUBE_API_KEY}&prettyPrint=false`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      context: { client: INNERTUBE_CLIENT },
      ...body,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Innertube ${endpoint} failed: ${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

// ─── Video Metadata ──────────────────────────────────────────────────────────

async function fetchVideoPage(videoId) {
  const resp = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9",
    },
  });
  if (!resp.ok) throw new Error(`Failed to fetch video page: ${resp.status}`);
  return resp.text();
}

function extractInitialData(html) {
  const match = html.match(/var ytInitialData\s*=\s*({.+?});\s*<\/script>/);
  if (match) {
    try {
      return JSON.parse(match[1]);
    } catch {}
  }
  return null;
}

function extractPlayerResponse(html) {
  const match = html.match(
    /var ytInitialPlayerResponse\s*=\s*({.+?});\s*(?:var|<\/script>)/
  );
  if (match) {
    try {
      return JSON.parse(match[1]);
    } catch {}
  }
  return null;
}

async function getVideoMetadata(videoId) {
  const html = await fetchVideoPage(videoId);
  const player = extractPlayerResponse(html);
  const initialData = extractInitialData(html);

  if (!player || !player.videoDetails) {
    throw new Error("Could not extract video metadata");
  }

  const details = player.videoDetails;
  const microformat = player.microformat?.playerMicroformatRenderer || {};

  // Extract engagement metrics from initialData
  let metrics = {};
  try {
    const contents =
      initialData?.contents?.twoColumnWatchNextResults?.results?.results
        ?.contents;
    if (contents) {
      for (const item of contents) {
        const primary = item.videoPrimaryInfoRenderer;
        if (primary) {
          const viewCount =
            primary.viewCount?.videoViewCountRenderer?.viewCount?.simpleText;
          if (viewCount) metrics.views = viewCount;

          // Like count from top-level buttons
          const buttons =
            primary.videoActions?.menuRenderer?.topLevelButtons || [];
          for (const btn of buttons) {
            const toggle =
              btn.segmentedLikeDislikeButtonViewModel?.likeButtonViewModel
                ?.likeButtonViewModel?.toggleButtonViewModel
                ?.toggleButtonViewModel?.defaultButtonViewModel
                ?.buttonViewModel;
            if (toggle?.title) {
              metrics.likes = toggle.title;
            }
          }
          break;
        }
      }
    }
  } catch {}

  // Extract description
  let description = details.shortDescription || "";

  // Extract chapters from description
  const chapters = [];
  const chapterRegex = /(\d{1,2}:\d{2}(?::\d{2})?)\s+(.+)/g;
  let chapterMatch;
  while ((chapterMatch = chapterRegex.exec(description))) {
    chapters.push({ time: chapterMatch[1], title: chapterMatch[2].trim() });
  }

  return {
    id: details.videoId,
    title: details.title,
    author: details.author,
    channelId: details.channelId,
    duration: formatDuration(parseInt(details.lengthSeconds || "0")),
    durationSeconds: parseInt(details.lengthSeconds || "0"),
    views: metrics.views || details.viewCount,
    likes: metrics.likes,
    publishDate: microformat.publishDate,
    description,
    chapters: chapters.length > 0 ? chapters : undefined,
    keywords: details.keywords?.slice(0, 15),
    thumbnail: details.thumbnail?.thumbnails?.pop()?.url,
    isLive: details.isLiveContent,
  };
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// ─── Transcript ──────────────────────────────────────────────────────────────

// Fetch captions via the Innertube player API (ANDROID client returns working URLs)
async function fetchCaptionTracks(videoId) {
  // First get API key from page
  const html = await fetchVideoPage(videoId);
  const apiKeyMatch = html.match(/"INNERTUBE_API_KEY":\s*"([a-zA-Z0-9_-]+)"/);
  const apiKey = apiKeyMatch ? apiKeyMatch[1] : INNERTUBE_API_KEY;

  const resp = await fetch(
    `https://www.youtube.com/youtubei/v1/player?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        context: { client: INNERTUBE_CLIENT_ANDROID },
        videoId,
      }),
    }
  );
  if (!resp.ok) throw new Error(`Innertube player failed: ${resp.status}`);
  const data = await resp.json();

  const status = data.playabilityStatus?.status;
  if (status && status !== "OK") {
    throw new Error(
      `Video not playable: ${status} — ${data.playabilityStatus?.reason || "unknown"}`
    );
  }

  const captions =
    data.captions?.playerCaptionsTracklistRenderer?.captionTracks;
  if (!captions || captions.length === 0) {
    throw new Error(
      "No captions available for this video. Try download-audio + external transcription."
    );
  }
  return captions;
}

// Parse YouTube XML caption format
function parseCaptionXml(xml) {
  const segments = [];
  const regex = /<text start="([^"]*)" dur="([^"]*)"[^>]*>([\s\S]*?)<\/text>/g;
  let match;
  while ((match = regex.exec(xml))) {
    const startSec = parseFloat(match[1]);
    const dur = parseFloat(match[2]);
    let text = match[3];
    // Decode HTML entities
    text = text
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/<[^>]*>/g, "") // strip any HTML tags
      .replace(/\n/g, " ")
      .trim();
    if (text.length > 0) {
      segments.push({
        text,
        startMs: Math.round(startSec * 1000),
        start: formatTimestamp(Math.round(startSec * 1000)),
        duration: dur,
      });
    }
  }
  return segments;
}

async function getTranscript(videoId, lang = "en", includeTimestamps = false) {
  const captions = await fetchCaptionTracks(videoId);

  // Find the best matching caption track
  let track = captions.find((t) => t.languageCode === lang);
  if (!track) track = captions.find((t) => t.languageCode.startsWith(lang));
  if (!track) track = captions[0];

  // Clean up the URL — strip srv3 format, check for PoToken requirement
  let captionUrl = track.baseUrl.replace("&fmt=srv3", "");
  if (captionUrl.includes("&exp=xpe")) {
    throw new Error(
      "This video requires a PoToken for captions (anti-bot protection). Try download-subs with yt-dlp instead."
    );
  }

  const resp = await fetch(captionUrl);
  if (!resp.ok) throw new Error(`Failed to fetch captions: ${resp.status}`);
  const xml = await resp.text();
  if (!xml || xml.length === 0) {
    throw new Error("Caption response was empty. The video may have restricted captions.");
  }

  const segments = parseCaptionXml(xml);
  const fullText = segments.map((s) => s.text).join(" ");

  const langName =
    track.name?.simpleText || track.name?.runs?.[0]?.text || track.languageCode;

  const result = {
    videoId,
    language: track.languageCode,
    languageName: langName,
    isAutoGenerated: track.kind === "asr",
    availableLanguages: captions.map((t) => ({
      code: t.languageCode,
      name: t.name?.simpleText || t.name?.runs?.[0]?.text || t.languageCode,
      isAutoGenerated: t.kind === "asr",
    })),
  };

  if (includeTimestamps) {
    result.segments = segments;
  } else {
    result.text = fullText;
  }

  result.charCount = fullText.length;
  result.wordCount = fullText.split(/\s+/).length;

  return result;
}

function formatTimestamp(ms) {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0)
    return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// ─── Comments ────────────────────────────────────────────────────────────────

async function getComments(videoId, count = 20) {
  // Use innertube next endpoint to get comments continuation token
  const data = await innertubePost("next", { videoId });

  const contents =
    data?.contents?.twoColumnWatchNextResults?.results?.results?.contents;
  if (!contents) throw new Error("Could not find video contents");

  let commentsToken = null;
  for (const item of contents) {
    const section = item.itemSectionRenderer;
    if (section?.sectionIdentifier === "comment-item-section") {
      commentsToken =
        section.contents?.[0]?.continuationItemRenderer?.continuationEndpoint
          ?.continuationCommand?.token;
      break;
    }
  }

  if (!commentsToken) throw new Error("Could not find comments continuation token");

  // Fetch comments using the continuation token
  const commentsData = await innertubePost("next", {
    continuation: commentsToken,
  });

  // YouTube now uses frameworkUpdates with mutations for comment data
  const mutations =
    commentsData?.frameworkUpdates?.entityBatchUpdate?.mutations || [];

  const comments = [];
  for (const mutation of mutations) {
    const entity = mutation.payload?.commentEntityPayload;
    if (!entity) continue;
    if (comments.length >= count) break;

    const author = entity.author?.displayName || "";
    const text = entity.properties?.content?.content || "";
    const likes = entity.toolbar?.likeCountNotliked || "0";
    const publishedTime = entity.properties?.publishedTime || "";
    const replyCount = parseInt(entity.toolbar?.replyCount || "0");

    if (text) {
      comments.push({ author, text, likes, publishedTime, replyCount });
    }
  }

  return { videoId, count: comments.length, comments };
}

// ─── Search ──────────────────────────────────────────────────────────────────

async function searchYouTube(query, count = 10) {
  const data = await innertubePost("search", {
    query,
    params: "EgIQAQ%3D%3D", // filter: videos only
  });

  const sections =
    data?.contents?.twoColumnSearchResultsRenderer?.primaryContents
      ?.sectionListRenderer?.contents || [];

  const results = [];
  for (const section of sections) {
    const items = section.itemSectionRenderer?.contents || [];
    for (const item of items) {
      if (results.length >= count) break;
      const vid = item.videoRenderer;
      if (!vid) continue;

      results.push({
        id: vid.videoId,
        title: (vid.title?.runs || []).map((r) => r.text).join(""),
        author: vid.ownerText?.runs?.[0]?.text || "",
        channelHandle:
          vid.ownerText?.runs?.[0]?.navigationEndpoint?.browseEndpoint
            ?.canonicalBaseUrl?.replace("/", "") || "",
        duration: vid.lengthText?.simpleText || "LIVE",
        views: vid.viewCountText?.simpleText || vid.viewCountText?.runs?.map(r => r.text).join("") || "",
        publishedTime: vid.publishedTimeText?.simpleText || "",
        description: (vid.detailedMetadataSnippets?.[0]?.snippetText?.runs || [])
          .map((r) => r.text)
          .join(""),
        thumbnail: vid.thumbnail?.thumbnails?.pop()?.url,
      });
    }
  }

  return { query, count: results.length, results };
}

// ─── Channel ─────────────────────────────────────────────────────────────────

async function getChannel(handle) {
  handle = handle.replace(/^@/, "");
  const resp = await fetch(`https://www.youtube.com/@${handle}`, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9",
    },
  });
  if (!resp.ok) throw new Error(`Failed to fetch channel: ${resp.status}`);
  const html = await resp.text();
  const initialData = extractInitialData(html);

  if (!initialData) throw new Error("Could not extract channel data");

  const header =
    initialData.header?.c4TabbedHeaderRenderer ||
    initialData.header?.pageHeaderRenderer;
  const metadata = initialData.metadata?.channelMetadataRenderer;

  if (!metadata) throw new Error("Could not extract channel metadata");

  // Try to get subscriber count from header
  let subscriberCount;
  if (header?.subscriberCountText?.simpleText) {
    subscriberCount = header.subscriberCountText.simpleText;
  }

  return {
    name: metadata.title,
    handle: `@${handle}`,
    channelId: metadata.externalId,
    description: metadata.description,
    subscriberCount,
    thumbnail: metadata.avatar?.thumbnails?.pop()?.url,
    url: metadata.channelUrl,
    keywords: metadata.keywords,
  };
}

async function getChannelVideos(handle, count = 10) {
  handle = handle.replace(/^@/, "");
  const resp = await fetch(`https://www.youtube.com/@${handle}/videos`, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9",
    },
  });
  if (!resp.ok) throw new Error(`Failed to fetch channel videos: ${resp.status}`);
  const html = await resp.text();
  const initialData = extractInitialData(html);

  if (!initialData) throw new Error("Could not extract channel data");

  // Navigate to the videos tab
  const tabs =
    initialData.contents?.twoColumnBrowseResultsRenderer?.tabs || [];
  let videosTab = null;
  for (const tab of tabs) {
    const t = tab.tabRenderer;
    if (t?.title === "Videos" && t.selected) {
      videosTab = t;
      break;
    }
  }

  if (!videosTab) throw new Error("Could not find Videos tab");

  const items =
    videosTab.content?.richGridRenderer?.contents || [];

  const videos = [];
  for (const item of items) {
    if (videos.length >= count) break;
    const vid = item.richItemRenderer?.content?.videoRenderer;
    if (!vid) continue;

    videos.push({
      id: vid.videoId,
      title: (vid.title?.runs || []).map((r) => r.text).join(""),
      duration: vid.lengthText?.simpleText || "LIVE",
      views: vid.viewCountText?.simpleText || "",
      publishedTime: vid.publishedTimeText?.simpleText || "",
      thumbnail: vid.thumbnail?.thumbnails?.pop()?.url,
    });
  }

  return {
    channel: `@${handle}`,
    count: videos.length,
    videos,
  };
}

// ─── Playlist ────────────────────────────────────────────────────────────────

async function getPlaylist(playlistId) {
  playlistId = extractPlaylistId(playlistId);
  const data = await innertubePost("browse", {
    browseId: `VL${playlistId}`,
  });

  const header =
    data?.header?.playlistHeaderRenderer;
  const contents =
    data?.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer
      ?.content?.sectionListRenderer?.contents?.[0]?.itemSectionRenderer
      ?.contents?.[0]?.playlistVideoListRenderer?.contents || [];

  const videos = [];
  for (const item of contents) {
    const vid = item.playlistVideoRenderer;
    if (!vid) continue;
    videos.push({
      id: vid.videoId,
      title: (vid.title?.runs || []).map((r) => r.text).join(""),
      author: vid.shortBylineText?.runs?.[0]?.text || "",
      duration: vid.lengthText?.simpleText || "",
      index: parseInt(vid.index?.simpleText || "0"),
    });
  }

  return {
    playlistId,
    title: header?.title?.simpleText || "",
    videoCount: header?.numVideosText?.runs?.map((r) => r.text).join("") || "",
    author: header?.ownerText?.runs?.[0]?.text || "",
    videos,
  };
}

// ─── URL Router ──────────────────────────────────────────────────────────────

async function handleUrl(url) {
  // Video
  const videoId = extractVideoId(url);
  if (videoId) {
    const [metadata, transcript] = await Promise.allSettled([
      getVideoMetadata(videoId),
      getTranscript(videoId),
    ]);
    const result = { type: "video" };
    if (metadata.status === "fulfilled") result.metadata = metadata.value;
    if (transcript.status === "fulfilled") result.transcript = transcript.value;
    else
      result.transcriptError = transcript.reason?.message || "Transcript unavailable";
    return result;
  }

  // Playlist
  if (url.includes("list=")) {
    return { type: "playlist", ...(await getPlaylist(url)) };
  }

  // Channel
  const channelMatch = url.match(/youtube\.com\/@([a-zA-Z0-9_.-]+)/);
  if (channelMatch) {
    const handle = channelMatch[1];
    const [info, videos] = await Promise.all([
      getChannel(handle),
      getChannelVideos(handle, 10),
    ]);
    return { type: "channel", ...info, recentVideos: videos.videos };
  }

  // Search
  const searchMatch = url.match(/youtube\.com\/results\?search_query=([^&]+)/);
  if (searchMatch) {
    const query = decodeURIComponent(searchMatch[1]);
    return await searchYouTube(query);
  }

  throw new Error("Could not parse YouTube URL: " + url);
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  const rawArgs = process.argv.slice(2);
  if (rawArgs.length === 0) {
    fail(
      "Usage: node youtube.mjs <command> [args]\nCommands: url, video, transcript, comments, search, channel, channel-videos, playlist"
    );
  }

  const command = rawArgs[0];
  const args = parseArgs(rawArgs.slice(1));

  try {
    switch (command) {
      case "url": {
        const url = args._[0];
        if (!url) fail("Usage: node youtube.mjs url <youtubeUrl>");
        out(await handleUrl(url));
        break;
      }

      case "video": {
        const id = extractVideoId(args._[0] || "");
        if (!id) fail("Usage: node youtube.mjs video <videoId>");
        out(await getVideoMetadata(id));
        break;
      }

      case "transcript": {
        const id = extractVideoId(args._[0] || "");
        if (!id) fail("Usage: node youtube.mjs transcript <videoId> [--lang en] [--timestamps]");
        const lang = args.lang || "en";
        const timestamps = !!args.timestamps;
        out(await getTranscript(id, lang, timestamps));
        break;
      }

      case "comments": {
        const id = extractVideoId(args._[0] || "");
        if (!id) fail("Usage: node youtube.mjs comments <videoId> [count]");
        const count = parseInt(args._[1] || "20");
        out(await getComments(id, count));
        break;
      }

      case "search": {
        const query = args._[0];
        if (!query) fail("Usage: node youtube.mjs search <query> [count]");
        const count = parseInt(args._[1] || "10");
        out(await searchYouTube(query, count));
        break;
      }

      case "channel": {
        const handle = args._[0];
        if (!handle) fail("Usage: node youtube.mjs channel <handle>");
        out(await getChannel(handle));
        break;
      }

      case "channel-videos": {
        const handle = args._[0];
        if (!handle) fail("Usage: node youtube.mjs channel-videos <handle> [count]");
        const count = parseInt(args._[1] || "10");
        out(await getChannelVideos(handle, count));
        break;
      }

      case "playlist": {
        const plId = args._[0];
        if (!plId) fail("Usage: node youtube.mjs playlist <playlistId>");
        out(await getPlaylist(plId));
        break;
      }

      default:
        fail(`Unknown command: ${command}. Run without arguments to see usage.`);
    }
  } catch (err) {
    fail(err.message);
  }
}

main();

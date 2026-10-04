#!/usr/bin/env python3
"""Build and QA pipeline for /devkit:page.

    pagekit.py init  BUILD [--with PART,...]          page.html from template.html plus the named parts
    pagekit.py build BUILD OUTPUT [--artifact PATH]   inline libraries, D2 diagrams and text includes
    pagekit.py qa    BUILD OUTPUT [--repo owner/name] mechanical QA, scripted interactions, screenshots

Parts (scripts/page/parts/NAME.html): tiles, d2, diff, toggle, steps, popover, chart, code.
init adds the libraries each part needs to devkit-libs.

page.html markers, replaced by `build`:
    <meta name="devkit-libs" content="diff2html,hljs,alpine,plot">   pinned CDN tags with SRI
    <!-- d2:NAME -->     BUILD/diagrams/NAME.d2 rendered to inline SVG (light + dark themes)
    <!-- text:PATH -->   HTML-escaped contents of BUILD/PATH (a diff, a code excerpt)
    <!-- PLAN ... -->    the section plan; removed from the output

--artifact PATH also writes a body-only copy for hosts that wrap the page in their own
skeleton (Claude Artifacts): <title> first, then styles, library tags and the body content.
"""
import base64
import hashlib
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/.cache/devkit-page")
ALLOWED_HOSTS = {"cdn.jsdelivr.net", "cdnjs.cloudflare.com", "fonts.googleapis.com", "fonts.gstatic.com"}
JSD = "https://cdn.jsdelivr.net/npm"
CDNJS = "https://cdnjs.cloudflare.com/ajax/libs"

# Pinned with SRI. To bump: change the URL, recompute with
#   curl -s URL | openssl dgst -sha384 -binary | openssl base64 -A
# Stylesheets are inlined at build time (checked against the SRI): Artifact hosts block
# external stylesheets except Google Fonts. highlight.js colors come from the template tokens.
LIBS = {
    "diff2html": [
        ("css", f"{JSD}/diff2html@3.4.56/bundles/css/diff2html.min.css",
         "sha384-PdRCG/+r1waybtXfuDB9Kmv2h7AGoN6WaTZ5OF+ctPeR9BGne0FaKRQnUeGV4nDL"),
        ("js", f"{JSD}/diff2html@3.4.56/bundles/js/diff2html-ui-slim.min.js",
         "sha384-WV/85F8QlW9zrU6tCec7YGnPJWFExGkFiGU9Ir/5QHjLhu1jcvhe8XoVdWsCLZ7b"),
    ],
    "hljs": [
        ("js", f"{CDNJS}/highlight.js/11.11.1/highlight.min.js",
         "sha384-RH2xi4eIQ/gjtbs9fUXM68sLSi99C7ZWBRX1vDrVv6GQXRibxXLbwO2NGZB74MbU"),
        ("js", f"{CDNJS}/highlight.js/11.11.1/languages/go.min.js",
         "sha384-HdearVH8cyfzwBIQOjL/6dSEmZxQ5rJRezN7spps8E7iu+R6utS8c2ab0AgBNFfH"),
    ],
    "plot": [
        ("js", f"{JSD}/d3@7.9.0/dist/d3.min.js",
         "sha384-CjloA8y00+1SDAUkjs099PVfnY2KmDC2BZnws9kh8D/lX1s46w6EPhpXdqMfjK6i"),
        ("js", f"{JSD}/@observablehq/plot@0.6.17/dist/plot.umd.min.js",
         "sha384-JUpn2GgRr0gxU0xOBd8D8P634jhRCwobtG8G2MMEkX1RnGJ7/FJNnuukpfT+H2w1"),
    ],
    # Alpine last and deferred: it must start after the page's own x-data helpers are defined.
    "alpine": [
        ("js-defer", f"{JSD}/alpinejs@3.17.4/dist/cdn.min.js",
         "sha384-5/joNqFnRyVWzXp99bHot6RHG+EksGp+USSgZwPar7T9SD9PKKER37n/8bXBAZGd"),
    ],
}

# Libraries each part needs; init writes their union to devkit-libs.
PARTS = {"tiles": [], "d2": [], "diff": ["diff2html"], "toggle": ["alpine"], "steps": ["alpine"],
         "popover": [], "chart": ["plot"], "code": ["hljs"]}


def fetch_pinned(url, sri):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, hashlib.sha256(url.encode()).hexdigest()[:24])
    data = open(path, "rb").read() if os.path.exists(path) else urllib.request.urlopen(url, timeout=30).read()
    got = "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()
    if got != sri:
        sys.exit(f"SRI mismatch for {url}: got {got}")
    open(path, "wb").write(data)
    return data.decode()


def lib_tags(names):
    unknown = set(names) - set(LIBS)
    if unknown:
        sys.exit(f"unknown libs in devkit-libs: {sorted(unknown)}; known: {sorted(LIBS)}")
    out = []
    for name in [n for n in LIBS if n in names]:
        for kind, url, sri in LIBS[name]:
            a = f'integrity="{sri}" crossorigin="anonymous"'
            if kind == "css":
                out.append(f"<style>/* {url} */\n{fetch_pinned(url, sri)}\n</style>")
            elif kind == "js":
                out.append(f'<script src="{url}" {a}></script>')
            elif kind == "js-defer":
                out.append(f'<script defer src="{url}" {a}></script>')
    return "\n".join(out)


def theme_d2(svg):
    """d2 puts its dark theme under a bare prefers-color-scheme query. Guard it so a host
    data-theme="light" wins, and repeat it under data-theme="dark" so a host toggle wins too."""
    m = re.search(r"@media screen and \(prefers-color-scheme:\s*dark\)\s*\{", svg)
    if not m:
        return svg
    i, depth = m.end(), 1
    while depth:
        depth += {"{": 1, "}": -1}.get(svg[i], 0)
        i += 1
    body = svg[m.end():i - 1]

    def scoped(prefix):
        return re.sub(r"([^{}]+)\{", lambda r: ",".join(
            f"{prefix} {s.strip()}" for s in r.group(1).split(",")) + "{", body)

    return (svg[:m.start()] + "@media screen and (prefers-color-scheme:dark){"
            + scoped(':root:not([data-theme="light"])') + "}" + scoped(':root[data-theme="dark"]') + svg[i:])


def render_d2(src):
    if not shutil.which("d2"):
        sys.exit("d2 is not installed: brew install d2 (Linux: curl -fsSL https://d2lang.com/install.sh | sh -s --)")
    out = src[:-3] + ".svg"
    r = subprocess.run(["d2", "--theme", "0", "--dark-theme", "200", "--layout", "elk", "--pad", "8",
                        src, out], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"d2 failed for {src}:\n{r.stderr}")
    svg = open(out).read()
    svg = re.sub(r"^<\?xml[^>]*\?>", "", svg).strip()
    # Scale to the container; the figure around it carries role/aria-label.
    return theme_d2(svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1))


def cmd_init(build, parts):
    unknown = [p for p in parts if p not in PARTS]
    if unknown:
        sys.exit(f"unknown parts: {unknown}; known: {sorted(PARTS)}")
    os.makedirs(os.path.join(build, "diagrams"), exist_ok=True)
    dst = os.path.join(build, "page.html")
    if os.path.exists(dst):
        sys.exit(f"{dst} exists; not overwriting")
    libs = [n for n in LIBS if any(n in PARTS[p] for p in parts)]
    snippets = []
    for p in parts:
        body = open(os.path.join(HERE, "parts", p + ".html")).read().rstrip("\n")
        snippets.append(f"  <!-- part: {p} (move into the section that needs it) -->\n"
                        + "\n".join("  " + line if line else line for line in body.splitlines()))
    src = open(os.path.join(HERE, "template.html")).read()
    src = src.replace("{{LIBS}}", ",".join(libs)).replace("{{PARTS}}", "\n\n".join(snippets))
    open(dst, "w").write(src)
    print(f"build dir ready: {build} (parts: {', '.join(parts) or 'none'}; libs: {', '.join(libs) or 'none'})")


def to_artifact(src):
    head = re.search(r"<head>(.*?)</head>", src, re.S).group(1)
    body = re.search(r"<body[^>]*>(.*)</body>", src, re.S).group(1)
    title = re.search(r"<title>.*?</title>", head, re.S).group(0)
    head = head.replace(title, "", 1)
    head = re.sub(r'<meta (?:charset|name="viewport")[^>]*>\s*|<link rel="icon"[^>]*>\s*', "", head)
    return f"{title}\n{head.strip()}\n{body.strip()}\n"


def cmd_build(build, out, artifact):
    src = open(os.path.join(build, "page.html")).read()
    src = re.sub(r"<!-- PLAN.*?-->\n?", "", src, flags=re.S)
    m = re.search(r'<meta name="devkit-libs" content="([^"]*)">', src)
    names = [n.strip() for n in (m.group(1).split(",") if m else []) if n.strip()]
    if m:
        src = src.replace(m.group(0), lib_tags(names))

    def d2(mt):
        path = os.path.join(build, "diagrams", mt.group(1) + ".d2")
        if not os.path.exists(path):
            sys.exit(f"missing diagram source: {path}")
        return render_d2(path)

    def text(mt):
        path = os.path.join(build, mt.group(1))
        if not os.path.exists(path):
            sys.exit(f"missing include: {path}")
        return html.escape(open(path).read().rstrip("\n"))

    src = re.sub(r"<!-- d2:([\w-]+) -->", d2, src)
    src = re.sub(r"<!-- text:([\w./-]+) -->", text, src)
    left = re.findall(r"<!-- (?:d2|text|part):[^>]*-->|\{\{[A-Z_]+\}\}", src)
    if left:
        sys.exit(f"unresolved markers, template placeholders or unplaced parts: {left[:5]}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w").write(src)
    print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB; libs: {', '.join(names) or 'none'})")
    if artifact:
        os.makedirs(os.path.dirname(os.path.abspath(artifact)), exist_ok=True)
        open(artifact, "w").write(to_artifact(src))
        print(f"wrote {artifact} (body-only, for Artifact publishing)")


# ---------------------------------------------------------------- QA

class Browser:
    def __init__(self, directory, fname, session):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        self.srv = subprocess.Popen([sys.executable, "-m", "http.server", str(self.port), "--bind", "127.0.0.1",
                                     "--directory", directory], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.url = f"http://127.0.0.1:{self.port}/{fname}"
        self.s = f"-s={session}"
        for _ in range(50):
            if subprocess.run(["curl", "-sf", self.url, "-o", "/dev/null"]).returncode == 0:
                break
            time.sleep(0.2)
        self.cli("open", self.url)

    def cli(self, *args):
        r = subprocess.run(["playwright-cli", self.s, *args], capture_output=True, text=True)
        return r.stdout + r.stderr

    def eval(self, js):
        out = self.cli("eval", js, "--raw").strip()
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return out

    def load(self, w, h, scheme):
        self.cli("resize", str(w), str(h))
        self.cli("set-color-scheme", scheme)
        self.cli("reload")
        time.sleep(1.0)

    def close(self):
        self.cli("close")
        self.srv.kill()


SENTENCES_JS = """() => {
  // Check each prose block on its own; quotes and code are source text, not page prose.
  const long = [];
  for (const el of document.querySelectorAll('p,li,figcaption,td,th,dd,dt,h1,h2,h3,summary')) {
    if (el.closest('blockquote,pre,code,.d2h-wrapper,[popover]:not(:popover-open)') && !el.matches('[popover] p')) continue;
    if (el.querySelector('p,li')) continue;  // only leaf blocks
    const t = el.textContent.replace(/\\s+/g, ' ').trim();
    for (const s of t.split(/(?<=[.!?])\\s+(?=[A-Z“"])/))
      if (s.split(' ').filter(Boolean).length > 25) long.push(s.slice(0, 120));
  }
  return long;
}"""

# y positions let qa map each finding to the screenshot tile that shows it.
LAYOUT_JS = """() => {
  const y = el => Math.round(el.getBoundingClientRect().top + scrollY);
  const bad = [];
  for (const el of document.querySelectorAll('h1,h2,h3,p,li,figcaption,button,td,th,dt,dd,.label')) {
    if (el.closest('pre,.d2h-wrapper,.scroll-x')) continue;
    if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX === 'visible')
      bad.push({t: el.tagName.toLowerCase() + ': ' + el.innerText.slice(0, 60), y: y(el)});
  }
  // Hidden panels (tabs, toggles) are not empty figures.
  const figs = [...document.querySelectorAll('figure')].filter(f => f.checkVisibility());
  const empty = figs.filter(f => f.getBoundingClientRect().height < 40).map(f => ({t: 'empty figure', y: y(f)}));
  return {overflow: bad.slice(0, 5), empty, figures: figs.map(y),
          scroll: document.documentElement.scrollWidth <= innerWidth,
          sw: document.documentElement.scrollWidth, iw: innerWidth};
}"""

LINKS_JS = """() => [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'))"""

# A page-state signature: visible text, ARIA state, open details and popovers.
SIG_JS = """const __sig = () => (document.querySelector('main') || document.body).innerText + '|' +
  [...document.querySelectorAll('[aria-selected],[aria-expanded],[aria-pressed]')]
    .map(e => [e.getAttribute('aria-selected'), e.getAttribute('aria-expanded'), e.getAttribute('aria-pressed')]).join() + '|' +
  [...document.querySelectorAll('details')].map(d => d.open ? 1 : 0).join('') + '|' +
  document.querySelectorAll(':popover-open').length;
const __label = el => (el.getAttribute('aria-label') || el.textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 40);
const __tick = () => new Promise(r => setTimeout(r, 80));
const __eligible = el => !el.closest('.d2h-wrapper, .steps-nav') && el.checkVisibility();"""

# Click every control and check that the page state changed. A selected tab waits until a
# sibling is selected. Step-through controls go to the last step and back to the first.
INTERACT_JS = """async () => {
  """ + SIG_JS + """
  const res = {controls: [], steps: []}, done = new Set();
  for (let pass = 0; pass < 3; pass++) {
    for (const el of document.querySelectorAll('button, summary, [role="tab"]')) {
      if (done.has(el) || !__eligible(el)) continue;
      if (el.disabled || el.getAttribute('aria-selected') === 'true') continue;
      done.add(el);
      const before = __sig(); el.click(); await __tick();
      res.controls.push({label: __label(el), ok: __sig() !== before});
      document.querySelectorAll(':popover-open').forEach(p => p.hidePopover());
      await __tick();
    }
  }
  const untested = [...document.querySelectorAll('button, summary, [role="tab"]')]
    .filter(el => !done.has(el) && __eligible(el)).map(__label);
  for (const nav of document.querySelectorAll('.steps-nav')) {
    if (!nav.checkVisibility()) continue;
    const b = nav.querySelectorAll('button'), prev = b[0], next = b[b.length - 1];
    let f = 0, r = 0;
    while (!next.disabled && f < 100) { next.click(); await __tick(); f++; }
    while (!prev.disabled && r < 100) { prev.click(); await __tick(); r++; }
    res.steps.push({label: __label(nav), forward: f, back: r, ok: f > 0 && f === r && prev.disabled && !next.disabled});
  }
  res.untested = untested;
  return res;
}"""

KEY_PREP_JS = """() => {
  """ + SIG_JS + """
  const el = [...document.querySelectorAll('[popovertarget], [role="tab"][aria-selected="false"], summary')]
    .find(e => __eligible(e) && !e.disabled);
  if (!el) return null;
  el.focus(); window.__qaSig = __sig();
  return __label(el);
}"""

KEY_CHECK_JS = """() => {
  """ + SIG_JS + """
  const ok = __sig() !== window.__qaSig;
  document.querySelectorAll(':popover-open').forEach(p => p.hidePopover());
  return ok;
}"""

# Force each host theme over the OS scheme: the page body (and a D2 diagram, if any) must follow.
THEME_JS = """() => {
  const r = document.documentElement;
  const look = () => {
    const f = document.querySelector('.d2 svg [class*="fill-"]');
    return [getComputedStyle(document.body).backgroundColor, f ? getComputedStyle(f).fill : null];
  };
  const base = look();
  r.dataset.theme = 'dark'; const dark = look();
  r.dataset.theme = 'light'; const light = look();
  delete r.dataset.theme;
  return {base, dark, light};
}"""


def tile(png, w, h):
    """Split a full-page screenshot into viewport-sized tiles: a 12000 px tall
    image is unreadable once an image reader scales it down."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=height", "-of", "csv=p=0", png],
                         capture_output=True, text=True).stdout.strip()
    total = int(out) if out.isdigit() else h
    th = tile_height(w, h)
    paths = []
    for i, y in enumerate(range(0, total, th)):
        t = png[:-4] + f"-{i + 1:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf", f"crop={w}:{min(th, total - y)}:0:{y}", t],
                       check=True)
        paths.append(t)
    return paths


def tile_height(w, h):
    return h * 2 if w < 800 else h  # phone tiles: two screens tall, still legible


def cmd_qa(build, out, repo):
    out = os.path.abspath(out)
    shots = os.path.join(build, "shots")
    os.makedirs(shots, exist_ok=True)
    session = "devkit-page-" + re.sub(r"\W", "", os.path.basename(out))[:30]
    br = Browser(os.path.dirname(out), os.path.basename(out), session)
    res = []
    try:
        errs, failed, hosts, scroll, layout, theme_bad = [], [], set(), {}, [], []
        all_tiles, to_read = 0, []

        def pick(paths, ys, th, why):
            for y in ys:
                p = paths[min(int(y // th), len(paths) - 1)]
                if p not in [t for t, _ in to_read]:
                    to_read.append((p, why))

        for w, h in ((1440, 900), (390, 844)):
            for scheme in ("light", "dark"):
                br.load(w, h, scheme)
                con = br.cli("console", "error")
                m = re.search(r"Errors: (\d+)", con)
                if not m or int(m.group(1)) > 0:
                    errs.append(f"{w}/{scheme}: " + " | ".join(
                        l for l in con.splitlines() if l.startswith(("[ERROR]", "Error")))[:300])
                for line in br.cli("requests", "--static").splitlines():
                    um = re.search(r"\] (https?://[^ ]+) =>", line)
                    if not um:
                        continue
                    host = re.sub(r"^https?://([^/:]+).*", r"\1", um.group(1))
                    if host != "127.0.0.1":
                        hosts.add(host)
                    if "[FAILED]" in line or re.search(r"=> \[[45]\d\d\]", line):
                        failed.append(line.strip()[:200])
                if w == 1440:
                    t = br.eval(THEME_JS)
                    other = "dark" if scheme == "light" else "light"
                    # Each part (page body, D2 diagram) must follow the forced theme on its own.
                    if not isinstance(t, dict) or any(
                            t[scheme][i] != t["base"][i] or (t["base"][i] is not None and t[other][i] == t["base"][i])
                            for i in range(2)):
                        theme_bad.append(f"OS {scheme}: {t}")
                lj = br.eval(LAYOUT_JS)
                p = os.path.join(shots, f"{w}-{scheme}.png")
                br.cli("screenshot", "--full-page", f"--filename={p}")
                paths = tile(p, w, h)
                all_tiles += len(paths)
                th = tile_height(w, h)
                if isinstance(lj, dict):
                    if w == 390:
                        scroll[scheme] = (lj["scroll"], lj["sw"], lj["iw"])
                    found = lj["overflow"] + lj["empty"]
                    if found:
                        layout.append(f"{w}/{scheme}: " + "; ".join(f["t"] for f in found))
                        pick(paths, [f["y"] for f in found], th, "flagged by layout scan")
                    if w == 390 and scheme == "dark":
                        pick(paths, lj["figures"], th, "figure at phone width")
                if (w, scheme) in ((1440, "light"), (390, "dark")):
                    pick(paths, [0], th, "sample")
        res.append(("1 clean load", "0 console errors, 0 failed requests" if not errs and not failed
                    else "; ".join(errs + failed)[:500], not errs and not failed))
        res.append(("2 screenshots", "4 taken; layout scan clean" if not layout
                    else "; ".join(layout)[:500], not layout))
        ok3 = all(v[0] for v in scroll.values()) and len(scroll) == 2
        res.append(("3 no horizontal scroll @390", ", ".join(f"{k}: {v[1]}<={v[2]}" for k, v in scroll.items()), ok3))

        br.load(1440, 900, "light")
        it = br.eval(INTERACT_JS)
        br.load(1440, 900, "light")
        key = br.eval(KEY_PREP_JS)
        key_ok = None
        if key:
            br.cli("press", "Enter")
            time.sleep(0.2)
            key_ok = br.eval(KEY_CHECK_JS) is True
        if isinstance(it, dict):
            bad = [c["label"] for c in it["controls"] if not c["ok"]] + [s["label"] for s in it["steps"] if not s["ok"]]
            if key_ok is False:
                bad.append(f"Enter on '{key}'")
            msg = (f"{len(it['controls'])} controls, {len(it['steps'])} step-throughs"
                   + (f", Enter on '{key}' ok" if key_ok else ", no keyboard target" if key is None else "")
                   + (f"; no state change: {bad[:5]}" if bad else "")
                   + (f"; not reached: {it['untested'][:5]}" if it["untested"] else ""))
            res.append(("4 interactions", msg, not bad and not it["untested"]))
        else:
            res.append(("4 interactions", f"script error: {str(it)[:300]}", False))

        links = br.eval(LINKS_JS) or []
        bad_links = [h for h in links if not re.match(r"^(https?://[^\s]+|#[\w-]+|mailto:\S+)$", h)]
        if repo:
            bad_links += [h for h in links if "github.com/" in h and f"github.com/{repo}" not in h
                          and "/kubernetes/community" not in h]
        ids = set(br.eval("() => [...document.querySelectorAll('[id]')].map(e => e.id)") or [])
        bad_links += [h for h in links if h.startswith("#") and h[1:] not in ids]
        res.append(("5 links well-formed", f"{len(links)} links" + (f"; bad: {bad_links[:5]}" if bad_links else ""),
                    not bad_links))
        size = os.path.getsize(out)
        foreign = sorted(hosts - ALLOWED_HOSTS)
        res.append(("6 hosts and size", f"hosts {sorted(hosts) or 'none'}; {size / 1024:.0f} KB",
                    not foreign and size < 2 * 1024 * 1024))
        long_s = br.eval(SENTENCES_JS) or []
        res.append(("7 sentence length ≤ 25 words", "all ok" if not long_s else f"{len(long_s)} long: {long_s[:3]}",
                    not long_s))
        res.append(("8 host theme override", "data-theme light/dark wins over the OS scheme" if not theme_bad
                    else "; ".join(map(str, theme_bad))[:400], not theme_bad))
    finally:
        br.close()
    print("| Check | Measured | Result |\n|---|---|---|")
    for n, v, ok in res:
        print(f"| {n} | {v} | {'PASS' if ok else 'FAIL'} |")
    print(f"\nTiles to read ({len(to_read)} of {all_tiles}; the rest are in {shots}):")
    print("\n".join(f"{p}  ({why})" for p, why in to_read))
    print("Still manual: every intent claim has a source on the page; no passive voice in headings and captions.")
    sys.exit(0 if all(r[2] for r in res) else 1)


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)

    def opt(name):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else None

    cmd, build = a[0], os.path.abspath(a[1])
    if cmd == "init":
        cmd_init(build, [p for p in (opt("--with") or "").split(",") if p])
    elif cmd == "build" and len(a) >= 3:
        cmd_build(build, a[2], opt("--artifact"))
    elif cmd == "qa" and len(a) >= 3:
        cmd_qa(build, a[2], opt("--repo"))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

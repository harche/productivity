#!/usr/bin/env python3
"""Build and QA pipeline for /devkit:page.

    pagekit.py init  BUILD                 copy template.html to BUILD/page.html
    pagekit.py build BUILD OUTPUT          inline libraries, D2 diagrams and text includes
    pagekit.py qa    BUILD OUTPUT [--repo owner/name]   mechanical QA checks + screenshots

page.html markers, replaced by `build`:
    <meta name="devkit-libs" content="diff2html,hljs,alpine,plot">   pinned CDN tags with SRI
    <!-- d2:NAME -->     BUILD/diagrams/NAME.d2 rendered to inline SVG (light + dark themes)
    <!-- text:PATH -->   HTML-escaped contents of BUILD/PATH (a diff, a code excerpt)
"""
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ALLOWED_HOSTS = {"cdn.jsdelivr.net", "cdnjs.cloudflare.com", "fonts.googleapis.com", "fonts.gstatic.com"}
JSD = "https://cdn.jsdelivr.net/npm"
CDNJS = "https://cdnjs.cloudflare.com/ajax/libs"

# Pinned with SRI. To bump: change the URL, recompute with
#   curl -s URL | openssl dgst -sha384 -binary | openssl base64 -A
LIBS = {
    "diff2html": [
        ("css", f"{JSD}/diff2html@3.4.56/bundles/css/diff2html.min.css",
         "sha384-PdRCG/+r1waybtXfuDB9Kmv2h7AGoN6WaTZ5OF+ctPeR9BGne0FaKRQnUeGV4nDL"),
        ("js", f"{JSD}/diff2html@3.4.56/bundles/js/diff2html-ui-slim.min.js",
         "sha384-WV/85F8QlW9zrU6tCec7YGnPJWFExGkFiGU9Ir/5QHjLhu1jcvhe8XoVdWsCLZ7b"),
    ],
    "hljs": [
        ("css-light", f"{CDNJS}/highlight.js/11.11.1/styles/github.min.css",
         "sha384-eFTL69TLRZTkNfYZOLM+G04821K1qZao/4QLJbet1pP4tcF+fdXq/9CdqAbWRl/L"),
        ("css-dark", f"{CDNJS}/highlight.js/11.11.1/styles/github-dark.min.css",
         "sha384-wH75j6z1lH97ZOpMOInqhgKzFkAInZPPSPlZpYKYTOqsaizPvhQZmAtLcPKXpLyH"),
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


def lib_tags(names):
    out = []
    for name in [n for n in LIBS if n in names]:
        for kind, url, sri in LIBS[name]:
            a = f'integrity="{sri}" crossorigin="anonymous"'
            if kind == "css":
                out.append(f'<link rel="stylesheet" href="{url}" {a}>')
            elif kind == "css-light":
                out.append(f'<link rel="stylesheet" href="{url}" {a} media="(prefers-color-scheme: light)">')
            elif kind == "css-dark":
                out.append(f'<link rel="stylesheet" href="{url}" {a} media="(prefers-color-scheme: dark)">')
            elif kind == "js":
                out.append(f'<script src="{url}" {a}></script>')
            elif kind == "js-defer":
                out.append(f'<script defer src="{url}" {a}></script>')
    unknown = set(names) - set(LIBS)
    if unknown:
        sys.exit(f"unknown libs in devkit-libs: {sorted(unknown)}; known: {sorted(LIBS)}")
    return "\n".join(out)


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
    return svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)


def cmd_init(build):
    os.makedirs(os.path.join(build, "diagrams"), exist_ok=True)
    dst = os.path.join(build, "page.html")
    if os.path.exists(dst):
        sys.exit(f"{dst} exists; not overwriting")
    shutil.copy(os.path.join(HERE, "template.html"), dst)
    print(f"build dir ready: {build} (edit page.html, put D2 sources in diagrams/)")


def cmd_build(build, out):
    src = open(os.path.join(build, "page.html")).read()
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
    left = re.findall(r"<!-- (?:d2|text):[^>]*-->|\{\{[A-Z_]+\}\}", src)
    if left:
        sys.exit(f"unresolved markers or template placeholders: {left[:5]}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w").write(src)
    print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB; libs: {', '.join(names) or 'none'})")


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

LAYOUT_JS = """() => {
  const bad = [];
  for (const el of document.querySelectorAll('h1,h2,h3,p,li,figcaption,button,td,th,dt,dd,.label')) {
    if (el.closest('pre,.d2h-wrapper,.scroll-x')) continue;
    if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX === 'visible')
      bad.push(el.tagName.toLowerCase() + ': ' + el.innerText.slice(0, 60));
  }
  // Hidden panels (tabs, toggles) are not empty figures.
  const empty = [...document.querySelectorAll('figure')].filter(f => f.checkVisibility() && f.getBoundingClientRect().height < 40).length;
  return {overflow: bad.slice(0, 5), emptyFigures: empty,
          scroll: document.documentElement.scrollWidth <= innerWidth,
          sw: document.documentElement.scrollWidth, iw: innerWidth};
}"""

LINKS_JS = """() => [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'))"""


def tile(png, w, h):
    """Split a full-page screenshot into viewport-sized tiles: a 12000 px tall
    image is unreadable once an image reader scales it down."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=height", "-of", "csv=p=0", png],
                         capture_output=True, text=True).stdout.strip()
    total = int(out) if out.isdigit() else h
    th = h * 2 if w < 800 else h  # phone tiles: two screens tall, still legible
    paths = []
    for i, y in enumerate(range(0, total, th)):
        t = png[:-4] + f"-{i + 1:02d}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf", f"crop={w}:{min(th, total - y)}:0:{y}", t],
                       check=True)
        paths.append(t)
    return paths


def cmd_qa(build, out, repo):
    out = os.path.abspath(out)
    shots = os.path.join(build, "shots")
    os.makedirs(shots, exist_ok=True)
    session = "devkit-page-" + re.sub(r"\W", "", os.path.basename(out))[:30]
    br = Browser(os.path.dirname(out), os.path.basename(out), session)
    res = []
    try:
        errs, failed, hosts, scroll, layout, shot_paths = [], [], set(), {}, [], []
        for w, h in ((1440, 900), (390, 844)):
            for scheme in ("light", "dark"):
                br.cli("resize", str(w), str(h))
                br.cli("set-color-scheme", scheme)
                br.cli("reload")
                time.sleep(1.0)
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
                lj = br.eval(LAYOUT_JS)
                if isinstance(lj, dict):
                    if w == 390:
                        scroll[scheme] = (lj["scroll"], lj["sw"], lj["iw"])
                    if lj["overflow"] or lj["emptyFigures"]:
                        layout.append(f"{w}/{scheme}: overflow={lj['overflow']} emptyFigures={lj['emptyFigures']}")
                p = os.path.join(shots, f"{w}-{scheme}.png")
                br.cli("screenshot", "--full-page", f"--filename={p}")
                shot_paths += tile(p, w, h)
        res.append(("1 clean load", "0 console errors, 0 failed requests" if not errs and not failed
                    else "; ".join(errs + failed)[:500], not errs and not failed))
        res.append(("2 screenshots", "4 taken; automatic layout scan clean" if not layout
                    else "; ".join(layout)[:500], not layout))
        ok3 = all(v[0] for v in scroll.values()) and len(scroll) == 2
        res.append(("3 no horizontal scroll @390", ", ".join(f"{k}: {v[1]}<={v[2]}" for k, v in scroll.items()), ok3))
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
    finally:
        br.close()
    print("| Check | Measured | Result |\n|---|---|---|")
    for n, v, ok in res:
        print(f"| {n} | {v} | {'PASS' if ok else 'FAIL'} |")
    print("\nScreenshot tiles (review every tile):\n" + "\n".join(shot_paths))
    print("Still manual: 4 interactions (snapshot + click + assert), 5 every intent claim has a source, "
          "7 no passive voice in headings and captions.")
    sys.exit(0 if all(r[2] for r in res) else 1)


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    cmd, build = a[0], os.path.abspath(a[1])
    if cmd == "init":
        cmd_init(build)
    elif cmd == "build" and len(a) >= 3:
        cmd_build(build, a[2])
    elif cmd == "qa" and len(a) >= 3:
        repo = a[a.index("--repo") + 1] if "--repo" in a else None
        cmd_qa(build, a[2], repo)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

---
description: Make a self-contained interactive HTML page with diagrams for a PR, issue or topic, in ASD-STE100
argument-hint: "<topic | this pr | this issue> [output-path]"
---

# Interactive page

REQUEST: $ARGUMENTS

Make one self-contained HTML page that explains the topic with real
diagrams and useful interactions. Do not hand it over until every check in
section 5 passes.

## 0. Parse REQUEST

- **Topic**: everything except a trailing output path.
  - `this pr`, `this issue`, `this`, a PR/issue URL or number: resolve as
    `/devkit:explain` section 1 does.
  - Anything else: a free-form topic. Read the code or docs it names, if any.
- **Output path**: a trailing token ending in `.html`, or a directory.
  Default: `~/Documents/pages/<slug>.html`. `<slug>` is kebab-case from the
  topic. Create the directory if missing.
- **Build dir**: `${TMPDIR:-/tmp}/devkit-page/<slug>/` for the plan,
  screenshots and QA scripts.

Work end to end without stopping for approval. Ask only if the topic itself
is ambiguous.

## 1. Preflight

QA uses `playwright-cli`:

```bash
command -v playwright-cli && playwright-cli --version
```

If it is missing, stop and print the install command
(`brew install playwright-cli`, or `npm install -g @playwright/cli` on Linux). If the browser is missing, run
`playwright-cli install-browser chromium`. Never skip QA.

## 2. Gather context

Use `/devkit:explain` sections 2–3 unchanged for a PR or issue. The same
rules apply: never invent motivation or a cause, and cite a source (body,
comment link, reviewer) for every claim about intent.

## 3. Plan

Write `plan.json`: an ordered list of sections, each
`{id, claim, prose, diagram?, interaction?, sources[]}`.

- `claim`: the one thing this section makes true for the reader.
- `diagram`: only if a picture shows the mechanism better than prose:
  sequence, state machine, data flow, structure, before/after. Describe
  the nodes and edges of the **actual** system, not generic boxes.
- `interaction`: only if changing state teaches something. Pick from:
  - step-through control for a sequence (prev / next / play, with a
    caption per step);
  - before/after tabs for a change;
  - hover or focus cards on code identifiers, which link to `file:line`
    (GitHub permalink at the PR head SHA when known);
  - collapsible diff hunks;
  - a toggle between scenarios (for example, with and without the fix).
- Decoration-only diagrams and interactions are not allowed. If a section
  needs neither, it gets neither.

Page structure for a PR or issue: the sections from `/devkit:explain`
section 4, plus a short "At a glance" summary at the top and a "Sources"
list at the end.

## 4. Build

One `.html` file. Inline CSS, JS and SVG. No build step.

- **Diagrams**: hand-written inline SVG with a `viewBox` that scales to the
  container. Use text, not images, for labels. Every diagram has a
  `<figcaption>` and a `<title>`/`aria-label` text alternative. Mermaid only
  for large generated graphs, loaded from cdnjs.cloudflare.com or
  cdn.jsdelivr.net.
- **External resources**: scripts only from cdnjs.cloudflare.com or
  cdn.jsdelivr.net, and fonts only from Google Fonts. Everything else
  inline. The page must still be readable if the CDN fails.
- **Theme**: define colors as tokens on `:root`. Override them under
  `@media (prefers-color-scheme: dark)`. Set an explicit `body` background.
  SVG strokes and fills use the tokens (`currentColor` or `var(--…)`), so
  diagrams work in both themes.
- **Layout**: a readable text column (about 70ch). Diagrams can be wider.
  At 390 px width: 16 px side padding, no horizontal page scroll. Wide
  diagrams scroll inside their own container.
- **Interactions**: plain JS, keyboard-accessible (buttons, not `div`s),
  and visible focus. The default state must make sense without JS.
- **Code**: identifiers in `<code>`. Diff excerpts in `<pre>` with
  added and removed lines colored by token.
- **Title**: a `<title>` of 2–4 words that names the subject.
- **Favicon**: an inline `<link rel="icon" href="data:,">` (or an inline
  SVG icon), so the browser does not log a 404 for `/favicon.ico`.

### Language: ASD-STE100

All prose, captions and labels in ASD-STE100 Simplified Technical English.

- One topic per sentence. Max 20 words for procedural sentences, max 25
  for descriptive sentences. Max 6 sentences per paragraph.
- Active voice. Simple tenses: present, past, future.
- Use the STE approved meaning of words ("make", "change", "use", "show").
  One word for one concept; do not use synonyms for variety.
- Use articles ("the", "a") where English permits.
- Technical names and code identifiers are allowed as they are.
- Use numbered lists for sequences and bullets for sets of items.
- No idioms, no phrasal verbs where a single verb exists, no "-ing" nouns
  when a verb works.

## 5. QA (all must pass before handover)

Run on the **final file** with `playwright-cli`. It blocks `file://`, so
serve the output directory on loopback, and use a named session so the
checks do not touch other browser sessions:

```bash
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory <output-dir> >/dev/null 2>&1 &
SRV=$!
until curl -sf "http://127.0.0.1:$PORT/<file>" >/dev/null; do sleep 0.2; done
S=-s=devkit-page-<slug>
URL="http://127.0.0.1:$PORT/<file>"
playwright-cli $S open "$URL"
```

Commands per check (repeat for each viewport and color scheme):

```bash
playwright-cli $S resize 1440 900                 # or 390 844
playwright-cli $S set-color-scheme light          # or dark
playwright-cli $S reload
playwright-cli $S console error                   # must report Errors: 0
playwright-cli $S requests --static               # no [FAILED], only allowed hosts
playwright-cli $S eval "() => document.documentElement.scrollWidth <= innerWidth" --raw
playwright-cli $S screenshot --full-page --filename=<build-dir>/shots/<w>-<scheme>.png
playwright-cli $S snapshot                        # refs for the controls to click
playwright-cli $S click <ref>                     # then eval/snapshot to assert a change
```

Always clean up, also after a failure:

```bash
playwright-cli $S close; kill "$SRV"
```

1. **Clean load**: zero console errors, zero failed network requests,
   zero uncaught exceptions.
2. **Screenshots**: full page at 1440×900 and 390×844, in light and dark
   (`set-color-scheme`). Look at all four with the image reader.
   Fail on: clipped or overlapping text, labels that run outside their
   shapes, unreadable contrast, empty diagram areas, broken layout.
3. **No horizontal scroll** at 390 px:
   `document.documentElement.scrollWidth <= innerWidth`.
4. **Interactions work**: find every control with `snapshot`, then
   `click` or `press` it. Use `eval` or a new `snapshot` to assert that the
   DOM or the SVG state changes. Step-through controls reach the last step
   and return. Take a screenshot of one mid-sequence state.
5. **Links and sources**: every `href` is well-formed. GitHub links match
   the target repo. Every intent claim in `plan.json` has its source on
   the page.
6. **Hosts and size**: the only external hosts are the allowed CDNs. The
   file is under 2 MB.
7. **Language**: no sentence over 25 words (`eval` over
   `document.body.innerText`), and no passive voice in headings and captions.

On a failure: fix the cause and run **all** checks again. After 3 full
rounds that still fail, stop and report the failing check with numbers.
Never hand over a page that fails.

## 6. Hand over

```bash
open <output>       # macOS
xdg-open <output>   # Linux
```

Report:

- Output path and file size.
- QA table: each check, measured value, pass/fail.
- Screenshot paths in the build dir.
- If the host has a publishing tool (for example Claude Artifacts), offer
  to publish in one line. Do not publish without a yes: a published
  page can be shared.

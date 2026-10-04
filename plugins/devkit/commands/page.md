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
- **Build dir**: `${TMPDIR:-/tmp}/devkit-page/<slug>/` for the page source,
  diagrams and screenshots.

Work end to end without stopping for approval. Ask only if the topic itself
is ambiguous.

## 1. Preflight

```bash
command -v playwright-cli d2 python3 ffmpeg
PK="${CLAUDE_PLUGIN_ROOT}/scripts/page"
[ -f "$PK/pagekit.py" ] || PK="$(dirname "$(ls -t ~/.claude/plugins/cache/*/devkit/*/scripts/page/pagekit.py | head -1)")"
```

`$PK` holds `pagekit.py` (init, build and QA), `template.html` (theme,
layout, pinned libraries) and `parts/` (one file per component). Use them;
do not rewrite them in the build dir. If one has a bug, fix it in the
plugin.

Missing tools: stop, print the install commands and offer to run them:
`brew install playwright-cli d2 ffmpeg` (Linux: `npm install -g @playwright/cli`,
`curl -fsSL https://d2lang.com/install.sh | sh -s --`). If the browser is
missing, run `playwright-cli install-browser chromium`. Never skip QA.

## 2. Gather context

Use `/devkit:explain` sections 2–3 unchanged for a PR or issue. The same
rules apply: never invent motivation or a cause, and cite a source (body,
comment link, reviewer) for every claim about intent.

## 3. Plan

Decide the ordered sections, each `id: claim | diagram? | interaction? |
sources`. You write this plan into the `<!-- PLAN -->` comment at the top
of `page.html` in section 4. There is no separate plan file.

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

Start the page with only the parts the plan uses:

```bash
python3 "$PK/pagekit.py" init <build-dir> --with d2,diff,steps,popover
```

| Part | Gives | Library (added to `devkit-libs` for you) | Fallback without JS or CDN |
|---|---|---|---|
| `d2` | Sequence, flow, structure, before/after diagram. Source in `diagrams/NAME.d2`. `build` renders it to inline SVG with light and dark themes and ELK layout. Use `direction: down` for anything with more than 3 nodes in a row. | D2 (build time) | Inline SVG: no JS needed |
| `diff` | PR diff, collapsed by default. Put the diff in `pr.diff` (`gh pr diff`). | diff2html | Raw diff in `<details><pre>` |
| `chart` | Metrics, numbers over time, comparisons. Only real data from the sources. | Observable Plot | `<table>` of the same data |
| `toggle` | Before/after tabs, scenario toggle | Alpine.js | All panels show, each with a heading |
| `steps` | Step-through for a sequence | Alpine.js | All steps show as a list |
| `popover` | Hover or focus card on an identifier | none (native `popover`) | The button text stays |
| `tiles` | Summary numbers | none | Plain HTML |
| `code` | Code excerpt, `<!-- text:excerpt.go -->` | highlight.js | Plain `<pre>` |

`init` puts each part's snippet after "At a glance", marked
`<!-- part: NAME -->`. Move each one into its section, remove the marker,
and repeat a snippet if the plan uses it more than once. `build` fails while
a marker is left. Hand-written SVG only for a mechanism that D2 cannot show
(for example, a row of CPU cells that change color).

Write the whole page in one edit where you can: plan comment, sections,
diagrams. Then build:

```bash
python3 "$PK/pagekit.py" build <build-dir> <output>
```

**Markers** that `build` replaces: `devkit-libs` (pinned CDN tags with SRI;
stylesheets are inlined), `<!-- d2:NAME -->`, `<!-- text:PATH -->`
(HTML-escaped file, for diffs and code). `build` removes the
`<!-- PLAN -->` comment. Put the diff source in a hidden `<textarea>`, as
the part does, not a `<script type="text/plain">`: escaped `&` stays
escaped there.

**Design.** The template gives a neutral GitHub-like theme. Change
`--accent` (and, if the subject calls for it, a display font from Google
Fonts) to suit the subject. Keep the three theme blocks (`:root`, the
`prefers-color-scheme` block guarded by `:not([data-theme="light"])`, and
`[data-theme="dark"]`) in step, so a host theme toggle works. Use colors
only through the tokens. Put at least one detail that only this subject
has (its real units, flags, terms of art) in the content.

**Rules that the template does not enforce:**

- Every diagram is in a `<figure>` with `role="img"`, an `aria-label` text
  alternative, and a `<figcaption>`.
- Interactions use buttons, not `div`s, and work from the keyboard.
- Identifiers in `<code>`. GitHub links are permalinks at the PR head SHA.
- `<title>`: 2–4 words that name the subject.

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

```bash
python3 "$PK/pagekit.py" qa <build-dir> <output> [--repo owner/name]
```

It serves the final file on loopback, uses its own `playwright-cli`
session, and prints a table. Layout checks run at 1440×900 and 390×844 in
light and dark:

1. **Clean load**: zero console errors, zero failed requests.
2. **Screenshots**: full page, split into tiles in `shots/`. A scan finds
   text that overflows its box and empty visible figures.
3. **No horizontal scroll** at 390 px.
4. **Interactions**: clicks every button, tab and `summary` and checks
   that the page state changes (visible text, ARIA state, open details or
   popovers). Walks each `.steps-nav` to the last step and back. Presses
   Enter on one control. Fails on a control with no effect, or one it
   could not reach.
5. **Links well-formed**: `href` syntax, `#anchors` exist, GitHub links
   match `--repo`.
6. **Hosts and size**: only cdn.jsdelivr.net, cdnjs.cloudflare.com and
   Google Fonts; file under 2 MB.
7. **Sentence length**: no prose sentence over 25 words (quotes and code
   are not checked).
8. **Host theme override**: a forced `data-theme` changes the page and
   any D2 diagram, in both directions.

Then do the checks that need judgment:

- **Read only the tiles that QA lists** under "Tiles to read": tiles with a
  layout finding, the phone tiles that show a figure, and one sample per
  width. Fail on clipped or overlapping text, labels outside their shapes,
  unreadable contrast, diagrams too small to read on the phone, broken
  layout. Read another tile only if you have a specific reason.
- **Sources**: every intent claim in the plan comment has its source on
  the page.
- **Language**: no passive voice in headings and captions.

On a failure: fix every cause in one pass, build again, and run `qa` once
more. Read only the tiles it lists for the changed areas. If a check still
fails after that one round, stop and report the failing check with
numbers. Never hand over a page that fails.

## 6. Hand over

```bash
open <output>       # macOS
xdg-open <output>   # Linux
```

Report:

- Output path and file size.
- The QA table from `pagekit.py qa`, plus the manual checks with what you
  tested.
- The `shots/` directory in the build dir.
- If the host has a publishing tool (for example Claude Artifacts), offer
  to publish in one line. Do not publish without a yes: a published
  page can be shared. On a yes, build a body-only copy and publish that
  file:

  ```bash
  python3 "$PK/pagekit.py" build <build-dir> <output> --artifact <build-dir>/artifact.html
  ```

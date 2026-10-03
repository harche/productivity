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

```bash
command -v playwright-cli d2 python3
PK="${CLAUDE_PLUGIN_ROOT}/scripts/page"
[ -f "$PK/pagekit.py" ] || PK="$(dirname "$(ls -t ~/.claude/plugins/cache/*/devkit/*/scripts/page/pagekit.py | head -1)")"
python3 "$PK/pagekit.py" init <build-dir>
```

`$PK` holds `pagekit.py` (build and QA) and `template.html` (theme, layout,
component patterns, pinned libraries). Use them; do not rewrite them in the
build dir. If one has a bug, fix it in the plugin.

Missing tools: stop, print the install commands and offer to run them:
`brew install playwright-cli d2` (Linux: `npm install -g @playwright/cli`,
`curl -fsSL https://d2lang.com/install.sh | sh -s --`). If the browser is
missing, run `playwright-cli install-browser chromium`. Never skip QA.

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

Edit `<build-dir>/page.html` (from `template.html`). It already has the
theme tokens (light and dark), the layout, the favicon, and commented
patterns for every component below. Keep the patterns the plan needs and
delete the rest.

**Use the libraries, not hand-made versions:**

| Need | Use | Fallback without JS or CDN |
|---|---|---|
| Sequence, flow, structure, before/after diagram | **D2**: source in `diagrams/NAME.d2`, `<!-- d2:NAME -->` in the page. `pagekit build` renders it to inline SVG with light and dark themes and ELK layout. Use `direction: down` for anything with more than 3 nodes in a row. | Inline SVG: no JS needed |
| PR diff | **diff2html**: put the diff in `pr.diff` (`gh pr diff`), use the diff pattern. It stays collapsed by default. | Raw diff in `<details><pre>` |
| Metrics, numbers over time, comparisons | **Observable Plot** (`plot` in `devkit-libs`). Only for real data from the sources. | `<table>` of the same data |
| Tabs, scenario toggle, step-through | **Alpine.js** (`alpine`): state in `x-data`, `x-show`. | All panels show, each with a heading |
| Hover or focus card on an identifier | Native `popover` + `popovertarget` button. No library. | The button text stays |
| Summary numbers | `.tiles` / `.tile` in the template | Plain HTML |
| Code excerpt | **highlight.js** (`hljs`), `<code class="language-go">`, `<!-- text:excerpt.go -->` | Plain `<pre>` |

Hand-written SVG only for a mechanism that D2 cannot show (for example, a
row of CPU cells that change color). Do not use a library that the plan
does not need: `devkit-libs` lists only the libraries in use.

**Markers** that `pagekit build` replaces: `devkit-libs` (pinned CDN tags
with SRI), `<!-- d2:NAME -->`, `<!-- text:PATH -->` (HTML-escaped file,
for diffs and code). Put the diff source in a hidden `<textarea>`, as the
pattern does, not a `<script type="text/plain">`: escaped `&` stays escaped
there.

```bash
python3 "$PK/pagekit.py" build <build-dir> <output>
```

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
session, and prints a table for the mechanical checks, at 1440×900 and
390×844 in light and dark:

1. **Clean load**: zero console errors, zero failed requests.
2. **Screenshots**: full page, split into viewport-sized tiles in
   `shots/`. It also scans for text that overflows its box and for empty
   visible figures.
3. **No horizontal scroll** at 390 px.
5. **Links well-formed**: `href` syntax, `#anchors` exist, GitHub links
   match `--repo`.
6. **Hosts and size**: only cdn.jsdelivr.net, cdnjs.cloudflare.com and
   Google Fonts; file under 2 MB.
7. **Sentence length**: no prose sentence over 25 words (quotes and code
   are not checked).

Then do the checks that need judgment:

- **Look at every tile** with the image reader. Fail on clipped or
  overlapping text, labels outside their shapes, unreadable contrast,
  diagrams too small to read on the phone tiles, broken layout.
- **4. Interactions**: open a `playwright-cli -s=<name>` session on a
  loopback server. Click every control (and press Enter on one with the
  keyboard). Use `eval` to assert the state changes: panels with
  `checkVisibility()`, popovers with `:popover-open`, `aria-selected` on
  tabs, `details.open`. Step-through controls reach the last step and
  return. Screenshot one changed state. In zsh, wrap the CLI in a function
  (`P() { playwright-cli -s=name "$@"; }`): `$P` with flags in a variable
  does not split.
- **5. Sources**: every intent claim in `plan.json` has its source on the
  page.
- **7. Language**: no passive voice in headings and captions.

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
- The QA table from `pagekit.py qa`, plus the manual checks (4, 5, 7) with
  what you tested.
- Screenshot paths in the build dir.
- If the host has a publishing tool (for example Claude Artifacts), offer
  to publish in one line. Do not publish without a yes: a published
  page can be shared.

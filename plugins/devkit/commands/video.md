---
description: Make a 3Blue1Brown-style narrated video explainer (Manim + OpenAI TTS) with audio QA
argument-hint: "<topic | this pr | this issue> [output-path]"
---

# Video explainer

REQUEST: $ARGUMENTS

Make a 3Blue1Brown-style video explainer: Manim animation, OpenAI TTS
narration, 1080p60 MP4, about 5–6 minutes. Do not hand it over until every
audio check in section 6 passes.

## 0. Parse REQUEST

- **Topic**: everything except a trailing output path.
  - `this pr`, `this issue`, a PR/issue URL or number: resolve and gather
    context exactly as `/devkit:explain` sections 1–3 do. The video explains
    that PR or issue; never invent motivation.
  - Anything else: a free-form topic. Read the code or docs it names, if any.
- **Output path**: a trailing token ending in `.mp4`, or a directory.
  Default: `~/Movies/<slug>.mp4` (macOS), `~/Videos/<slug>.mp4` (Linux).
  `<slug>` is kebab-case from the topic.
- **Build dir**: `${TMPDIR:-/tmp}/devkit-video/<slug>/`. Keep every
  intermediate file here so a re-run can resume.

Work end to end without stopping for approval. Ask only if the topic itself
is ambiguous. An empty REQUEST is ambiguous: ask, and offer the PR of the
current worktree or branch (if any) as the recommended option.

## 1. Preflight

```bash
command -v manim ffmpeg ffprobe python3 curl jq
VK="${CLAUDE_PLUGIN_ROOT}/scripts/video"
[ -f "$VK/vidkit.py" ] || VK="$(dirname "$(ls -t ~/.claude/plugins/cache/*/devkit/*/scripts/video/vidkit.py | head -1)")"
```

`$VK` holds the pipeline: `vidkit.py` (TTS, trimming, timeline, render,
assembly, QA), `base.py` (scene base class and palette) and `manim.cfg`.
Use them; do not rewrite them in the build dir. If one has a bug, fix it in
the plugin.

Missing tools: stop, print the install commands
(`brew install ffmpeg`, `uv tool install manim` or `pipx install manim`;
Linux: the distro `ffmpeg` package) and offer to run them. Only use
`MathTex`/`Tex` if `command -v latex` succeeds; otherwise use `Text`.

**API key.** Never print it, never write it to a file, never use `set -x`
or `curl -v`. Load it into the environment of the same command that uses it
(`vidkit.py clips` and `vidkit.py qa`); `vidkit.py` passes it to `curl` on
stdin, so it never appears in `argv`:

```bash
OPENAI_API_KEY="$(security find-generic-password -s OPENAI_API_KEY -w 2>/dev/null \
  || security find-generic-password -a OPENAI_API_KEY -w 2>/dev/null)"   # macOS
# Linux: existing $OPENAI_API_KEY, else: secret-tool lookup service OPENAI_API_KEY
```

If the lookup is empty, stop and say where the key was expected.

Then `python3 "$VK/vidkit.py" init <build>`.

## 2. Script

Write `<build>/script.json`: an ordered list of scenes, each
`{id, narration, visuals}`.

- 750–900 spoken words total (~150 wpm → 5–6 min). 8–14 scenes.
- 3Blue1Brown structure: start from a concrete question or puzzle, build
  intuition visually before naming things, one new idea per scene, end
  with a short recap of the key insight.
- `narration` is the text the viewer hears. Keep the original spelling
  (`CRI-O`). Write identifiers as words (`the restore test manager`), not
  camelCase; show the identifier on screen instead.
- `visuals` is the animation plan for that scene: what appears, moves,
  transforms or is highlighted, and when, in terms of the narration.

**Pronunciations.** Defaults in `vidkit.py`: `CRI-O` → `cry-o`, `kubelet` →
`cube-let`, `NUMA` → `noo-muh`, with the transcriber's usual misspellings
mapped back. For others the topic needs, write
`<build>/pronunciations.json`:
`{"pron": {"Kueue": "cue"}, "reverse": {"queue": "kueue"}}`. `reverse`
maps what Whisper writes back to the script's word.

## 3. Narration clips

```bash
OPENAI_API_KEY=... python3 "$VK/vidkit.py" clips <build>
python3 "$VK/vidkit.py" timeline <build>
```

`clips` makes one WAV per scene (`gpt-4o-mini-tts`, voice `marin`),
transcribes it, regenerates it on a mismatch (TTS truncation is common:
expect a few), and trims it: edge silence to 30 ms, inner pauses to 0.4 s.
Unchanged clips are cached. After 3 failed tries it stops. If the reported
"missing" text was misheard rather than dropped, add the spelling to
`reverse` and run it again.

`timeline` writes `timeline.json`, the single source of truth for video and
audio: each scene is `0.4 s lead-in + clip + 0.6 s tail`, in whole frames.
It warns if the total is outside 4:45–6:30; fix the script before
rendering.

## 4. Scenes

Write `<build>/scenes.py`:

```python
from base import *

class S01(Base):
    sid = "s01_puzzle"          # script.json id; classes in script order

    def construct(self):
        self.at("A pod is running")        # wait until the narration says it
        self.p(FadeIn(thing), rt=1.0)      # play, in whole frames
        ...
        self.finish()                      # fade out in the tail, exact length
```

- Time everything with `at`, `p`, `w` and `finish`. Do not call
  `self.play`/`self.wait` directly: `base.py` pads run times by half a
  frame so every scene has exactly the frame count of the timeline.
- 3Blue1Brown look: the `base.py` palette (`BLUE`, `YELLOW`, `TEAL`, `RED`,
  `GREEN`, `GREY` on a dark background), smooth `Transform`/`Create`/
  `FadeIn`, minimal on-screen text, diagrams built up step by step. No
  stock images and no walls of text.
- Let Manim do the layout:
  - Code: `code(src)` (Manim `Code`, syntax highlighted). For one line
    with coloured parts, `C(s, t2c={...})`; its submobjects skip spaces.
  - Tables: `Table`. Trees and graphs: `tree(...)` (`Graph`,
    `layout="tree"`) with `box()` vertices, which are opaque so edges do not
    cross labels.
  - Rows and grids: `arrange`, `arrange_in_grid`, `next_to`; braces and
    highlights: `Brace`, `SurroundingRectangle`; anything wide: `fit(m)`.
  - Icons: `SVGMobject`, e.g. the Kubernetes icon set in
    `kubernetes/community` (`icons/svg`).

```bash
python3 "$VK/vidkit.py" lint <build>              # classes match timeline, cues exist and are in order
python3 "$VK/vidkit.py" render <build> --preview  # -ql render + preview/sheet.png
```

Look at `preview/sheet.png` (one frame per scene, 0.9 s before its end) for
overlaps and text off the frame. Fix and preview again before the full
render.

## 5. Render and assemble

```bash
python3 "$VK/vidkit.py" render <build>              # 1080p60, 4 in parallel, checks frame counts
python3 "$VK/vidkit.py" assemble <build> <output>   # concat, mix audio at clip starts, mux
```

## 6. Audio QA (all must pass before handover)

```bash
OPENAI_API_KEY=... python3 "$VK/vidkit.py" qa <build> <output>
```

It checks the **final MP4** and prints a table:

1. **Durations match**: video and audio streams agree within one frame.
2. **Transcript complete**: Whisper transcript of the final audio matches
   the whole script in order, with nothing missing, repeated or extra.
3. **In sync**: each scene's voice starts within ±0.3 s of its timeline
   slot, measured from the audio (Whisper timestamps are too coarse).
4. **No dropouts**: no silence of 0.7 s or more inside a clip, and no gap
   longer than `tail + lead_in + 0.2 s` between clips.
5. **Format**: 1920x1080, 60 fps, H.264 + AAC, 4:45–6:30.

On a failure: fix the cause (pronunciation map, script, scene timing, or a
bug in `$VK`), rerun the affected steps, then run **all** checks again.
After 3 full rounds that still fail, stop and report the failing check with
numbers. Never hand over a file that fails.

## 7. Hand over

```bash
open -a "QuickTime Player" <output>   # macOS
xdg-open <output>                      # Linux
```

Report:

- Output path, duration, file size.
- The QA table from `vidkit.py qa`.
- Pronunciations applied.
- Build dir (for edits and re-runs).

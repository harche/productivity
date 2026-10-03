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
is ambiguous.

## 1. Preflight

```bash
command -v manim ffmpeg ffprobe python3 curl jq
```

Missing tools: stop and print the install commands
(`brew install ffmpeg`, `uv tool install manim` or `pipx install manim`;
Linux: the distro `ffmpeg` package). Only use `MathTex`/`Tex` if
`command -v latex` succeeds; otherwise use `Text`/`MarkupText`.

**API key.** Never print it, never write it to a file, never use `set -x`
or `curl -v`. Load it into the environment of the same command that uses it:

```bash
OPENAI_API_KEY="$(security find-generic-password -s OPENAI_API_KEY -w 2>/dev/null \
  || security find-generic-password -a OPENAI_API_KEY -w 2>/dev/null)"   # macOS
# Linux: existing $OPENAI_API_KEY, else: secret-tool lookup service OPENAI_API_KEY
```

If the lookup is empty, stop and say where the key was expected.

## 2. Script

Write `script.json`: an ordered list of scenes, each
`{id, narration, visuals}`.

- 750–900 spoken words total (~150 wpm → 5–6 min). 8–14 scenes.
- 3Blue1Brown structure: start from a concrete question or puzzle, build
  intuition visually before naming things, one new idea per scene, end
  with a short recap of the key insight.
- `narration` is the text the viewer hears. Keep the original spelling
  (`CRI-O`), and apply pronunciations only in section 3.
- `visuals` is the animation plan for that scene: what appears, moves,
  transforms or is highlighted, and when, in terms of the narration.

## 3. Narration clips

One clip per scene, from `POST https://api.openai.com/v1/audio/speech`:

```json
{
  "model": "gpt-4o-mini-tts",
  "voice": "marin",
  "input": "<narration with pronunciations applied>",
  "instructions": "Calm, curious explainer. Measured pace. Spell acronyms smoothly.",
  "response_format": "wav"
}
```

- Use WAV, not MP3: MP3 encoder padding breaks sample-exact timing.
- **Pronunciations**: apply to `input` only. Defaults:
  `CRI-O` → `cry-o`. Add others the topic needs (project names,
  acronyms that are words) and list them in the final report.
- Save as `clips/<id>.wav`. Skip a clip that exists and whose
  `narration` hash has not changed.
- **Per-clip check**: transcribe each clip (section 6 transcription call).
  Compare it to its narration after normalizing case, punctuation and the
  pronunciation map in reverse. If it is truncated, has extra words, or
  drops a sentence, regenerate it (max 3 tries, then fail loudly).

## 4. Timeline

Measure every clip with `ffprobe -show_entries format=duration`. Write
`timeline.json`:

- `scene_duration = lead_in (0.4s) + clip_duration + tail (0.6s)`, rounded
  up to a whole frame (1/60 s).
- `start` of each scene = sum of previous scene durations.
- The clip starts at `start + lead_in`.

This file is the single source of truth for both video and audio.

## 5. Render and assemble

**Animation** (`scenes.py`, Manim Community):

- One `Scene` class per script scene. Each reads its duration from
  `timeline.json`. The `run_time` values plus `wait()` must add up to
  exactly that duration. Finish with `self.wait(remaining)` and assert
  that `remaining >= 0`.
- 3Blue1Brown look: dark background, a small consistent palette (blue,
  yellow, teal, red for contrast), smooth `Transform`/`ReplacementTransform`/
  `Create`/`FadeIn`, minimal on-screen text, build diagrams up step by step.
  No stock images and no walls of text.
- Render: `manim -qh --fps 60 -r 1920,1080 scenes.py <Scene>`.

**Video**: concat the scene renders in order (ffmpeg concat demuxer,
`-c copy`) → `video.mp4`.

**Audio**: one track, built from the timeline. Place each clip at its
start with `adelay` and mix with `amix=normalize=0`, then `apad` and
`-t <video_duration>` so the track has exactly the video's length. Write
48 kHz WAV.

**Mux**:

```bash
ffmpeg -i video.mp4 -i narration.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 192k -t <video_duration> -movflags +faststart <output>
```

## 6. Audio QA (all must pass before handover)

Run every check on the **final MP4**, not the intermediates.

1. **Durations match**: `ffprobe` per-stream `duration` for video and
   audio. They must agree within one video frame (≤ 16.7 ms). This is the
   tightest limit AAC framing allows. Report both values.
2. **Every clip present and complete**: transcribe the final audio with
   `POST /v1/audio/transcriptions`, `model=whisper-1`,
   `response_format=verbose_json`, `timestamp_granularities[]=segment`.
   - The normalized transcript must match the full script in order, with
     no missing, repeated or extra sentences. Small transcription spelling
     differences (`cryo` vs `CRI-O`) are fine through the pronunciation map.
3. **In sync**: for each scene, the first transcribed segment of its
   narration starts within ±0.3 s of `start + lead_in` in the timeline.
4. **No dropouts**: `ffmpeg -i <output> -af silencedetect=noise=-45dB:d=0.7 -f null -`.
   Any silence that starts inside a clip's spoken window is a failure.
   Silence between clips is fine if it is no longer than the planned
   `tail + lead_in` + 0.2 s.
5. **Format**: `ffprobe` shows 1920x1080, 60 fps, H.264 + AAC, and a total
   duration between 4:45 and 6:30.

On a failure: fix the cause (regenerate the clip, fix the timeline, re-mux),
then run **all** checks again. After 3 full rounds that still fail, stop and
report the failing check with numbers. Never hand over a file that fails.

## 7. Hand over

```bash
open -a "QuickTime Player" <output>   # macOS
xdg-open <output>                      # Linux
```

Report:

- Output path, duration, file size.
- QA table: each check, measured value, pass/fail.
- Pronunciations applied.
- Build dir (for edits and re-runs).

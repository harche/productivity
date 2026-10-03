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
```

Missing tools: stop, print the install commands
(`brew install ffmpeg`, `uv tool install manim` or `pipx install manim`;
Linux: the distro `ffmpeg` package) and offer to run them. After installing
Manim, render a one-line `Text` scene to prove Cairo/Pango work. Only use `MathTex`/`Tex` if
`command -v latex` succeeds; otherwise use `Text`/`MarkupText`.

**API key.** Never print it, never write it to a file, never use `set -x`
or `curl -v`. Load it into the environment of the same command that uses it:

```bash
OPENAI_API_KEY="$(security find-generic-password -s OPENAI_API_KEY -w 2>/dev/null \
  || security find-generic-password -a OPENAI_API_KEY -w 2>/dev/null)"   # macOS
# Linux: existing $OPENAI_API_KEY, else: secret-tool lookup service OPENAI_API_KEY
```

If the lookup is empty, stop and say where the key was expected.

Pass the key to `curl` on stdin, so it never appears in `argv` (`ps`):
`printf 'Authorization: Bearer %s\n' "$OPENAI_API_KEY" | curl -sS --fail-with-body -H @- ...`.
Put request bodies in a file (`--data-binary @req.json`).

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
  Compare it to its narration (see **Text matching** below). If it is
  truncated, has extra words, or drops a sentence, regenerate it (max 3
  tries, then fail loudly). TTS truncation is common: expect the last
  sentence to go missing on a few clips per video.
- **Trim** every passing clip to `clips/<id>.trim.wav` **before** the
  timeline is built, so trimming never forces a re-render:
  - Edge silence (leading and trailing) → 30 ms. TTS often adds up to
    0.5 s at the start, which shifts the voice off its timeline slot.
  - Inner pauses longer than 0.4 s → 0.4 s (keep 0.2 s on each side).
    TTS puts 0.7–1.1 s pauses between sentences, which check 4 counts as
    dropouts. Regenerating does not reliably remove them.
  - Find silences with `silencedetect=noise=-45dB:d=0.05` and cut the
    PCM samples directly (convert to `pcm_s16le` first; Python `wave` is
    enough). `silenceremove` with `stop_periods=-1` does not shorten inner
    pauses reliably.
  - Afterwards assert that `silencedetect=noise=-45dB:d=0.7` finds no
    inner silence in the trimmed clip.

**Text matching** (per-clip check and check 2):

- Normalize both sides: lower case, `-` → space, drop punctuation, digits
  0–10 → words, `N-1` → `n minus one`, then the reverse pronunciation map
  on word boundaries.
- The reverse map holds the transcriber's spellings, not only the TTS
  spelling: e.g. `cubelet`/`cube let` → `kubelet`; `noma`/`nooma`/`pneuma`
  → `numa`. Add new ones when a check reports a misheard word.
- Pass if word-level `difflib` similarity ≥ 0.9 (0.93 for the full video),
  word-count ratio within ±7 % (±4 % for the full video), and every
  sentence is found in order at similarity ≥ 0.7. Compare in units of at
  least 6 words (merge a shorter sentence with the next one): one misheard
  word in `One NUMA node.` scores 0.67 and fails as a "missing" sentence.

## 4. Timeline

Measure every **trimmed** clip with `ffprobe -show_entries format=duration`. Write
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
- **Frame-exact timing.** Count time in whole frames, not seconds. Manim
  rounds differently per call: `play()` renders
  `len(np.arange(0, run_time, 1/fps))` frames and a static `wait()`
  renders `int(duration*fps)`, so plain `n/60` loses a frame now and then.
  For `n` frames use `play(..., run_time=(n - 0.5)/60)` and
  `wait((n + 0.5)/60, frozen_frame=True)`.
- **Cues from the narration.** Use a base class with `at("phrase")`: wait
  until `lead_in + clip_duration * index(phrase)/len(narration)`, then
  play. Check that every cue phrase is in its narration before rendering.
  End each scene with a 0.4 s fade-out inside the tail.
- `Text` submobjects skip spaces: index glyphs without counting spaces
  when you highlight part of a code string.
- **Preview first.** Render all scenes at `-ql`, take the frame 0.9 s
  before the end of each, tile them with `ffmpeg -vf tile=3x4`, and look
  at the sheet for overlaps and text off the frame before the HQ render.
- 3Blue1Brown look: dark background, a small consistent palette (blue,
  yellow, teal, red for contrast), smooth `Transform`/`ReplacementTransform`/
  `Create`/`FadeIn`, minimal on-screen text, build diagrams up step by step.
  No stock images and no walls of text.
- Render: `manim -qh --fps 60 -r 1920,1080 scenes.py <Scene>`. Scenes are
  independent; render 4 in parallel (`xargs -P 4`).
- Before concat, check every scene's frame count
  (`ffprobe -count_packets -show_entries stream=nb_read_packets`) against
  `round(duration * 60)` from the timeline. Any mismatch moves all later
  audio out of sync.

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
2. **Every clip present and complete**: extract the audio track with
   `-vn -c:a copy` to `.m4a` (no re-encode, under the 25 MB limit) and
   transcribe it with `POST /v1/audio/transcriptions`, `model=whisper-1`,
   `response_format=verbose_json`.
   - The normalized transcript must match the full script in order, with
     no missing, repeated or extra sentences (see **Text matching**).
3. **In sync**: for each scene, the voice onset is within ±0.3 s of
   `start + lead_in` in the timeline. Measure the onset from the audio,
   not from Whisper: run `silencedetect=noise=-45dB:d=0.3` on the final
   MP4 and take the `silence_end` nearest to the clip start, between the
   end of the previous clip and clip start + 1 s. No `silence_end` in that
   window is a failure. Whisper timestamps cannot measure ±0.3 s: whisper-1
   segments run back to back, so a segment's start includes the silence
   before it, and word timestamps drift by up to 2 s. Check 2 already
   proves that the words of each scene are present and in order.
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

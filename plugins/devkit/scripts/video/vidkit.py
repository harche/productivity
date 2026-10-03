#!/usr/bin/env python3
"""Build pipeline for /devkit:video.

    vidkit.py init     BUILD            copy base.py and manim.cfg into BUILD
    vidkit.py clips    BUILD            TTS each scene, verify, trim     (needs OPENAI_API_KEY)
    vidkit.py timeline BUILD            write timeline.json from trimmed clips
    vidkit.py lint     BUILD            scenes.py matches timeline; cue phrases exist
    vidkit.py render   BUILD [--preview]  render scenes (preview: -ql + contact sheet)
    vidkit.py assemble BUILD OUTPUT     concat video, mix audio, mux
    vidkit.py qa       BUILD OUTPUT     audio QA on the final MP4       (needs OPENAI_API_KEY)

BUILD holds script.json and, optionally, pronunciations.json:
    {"pron": {"CRI-O": "cry-o"}, "reverse": {"cryo": "cri o"}}
"reverse" maps transcriber spellings back to the script's (normalized) words.

OPENAI_API_KEY is passed to curl on stdin, so it never appears in argv or on disk.
"""
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 60
LEAD_IN, TAIL = 0.4, 0.6
TTS = {"model": "gpt-4o-mini-tts", "voice": "marin",
       "instructions": "Calm, curious explainer. Measured pace. Spell acronyms smoothly.",
       "response_format": "wav"}
PRON = {"CRI-O": "cry-o", "kubelet": "cube-let", "NUMA": "noo-muh"}
REVERSE = {"cryo": "cri o", "cry o": "cri o",
           "cubelet": "kubelet", "cube let": "kubelet", "kublet": "kubelet", "kube let": "kubelet",
           "noomah": "numa", "noo muh": "numa", "nooma": "numa", "noma": "numa", "pneuma": "numa"}
NUMS = "zero one two three four five six seven eight nine ten".split()


# ---------------------------------------------------------------- helpers

class Build:
    def __init__(self, path):
        self.dir = os.path.abspath(path)
        p = self.p("pronunciations.json")
        extra = json.load(open(p)) if os.path.exists(p) else {}
        self.pron = {**PRON, **extra.get("pron", {})}
        self.reverse = {**REVERSE, **extra.get("reverse", {})}

    def p(self, *parts):
        return os.path.join(self.dir, *parts)

    def script(self):
        return json.load(open(self.p("script.json")))

    def timeline(self):
        return json.load(open(self.p("timeline.json")))

    def clip(self, sid, trimmed=False):
        return self.p("clips", f"{sid}.trim.wav" if trimmed else f"{sid}.wav")

    def apply_pron(self, text):
        for k, v in self.pron.items():
            text = re.sub(rf"\b{re.escape(k)}\b", v, text)
        return text

    def norm(self, text):
        t = text.lower().replace("’", "'")
        t = re.sub(r"\bn\s*-\s*1\b", "n minus one", t)
        t = t.replace("-", " ")
        for k, v in self.reverse.items():
            t = re.sub(rf"\b{re.escape(k)}\b", v, t)
        t = re.sub(r"[^a-z0-9' ]+", " ", t)
        out = []
        for w in t.split():
            w = w.replace("'", "")
            if w.isdigit() and int(w) <= 10:
                w = NUMS[int(w)]
            out.append(w)
        return out

    def units(self, text):
        """Sentences merged up to >= 6 words: one misheard word in a
        3-word sentence must not read as a missing sentence."""
        out, cur = [], ""
        for s in re.split(r"(?<=[.?!:])\s+", text):
            cur = f"{cur} {s}".strip()
            if len(self.norm(cur)) >= 6:
                out.append(cur)
                cur = ""
        if cur:
            if out:
                out[-1] += " " + cur
            else:
                out.append(cur)
        return out

    def match(self, ref, hyp, min_ratio, max_len_dev):
        a, b = self.norm(ref), self.norm(hyp)
        ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        lenr = len(b) / max(1, len(a))
        missing, pos = [], 0
        for u in self.units(ref):
            uw = self.norm(u)
            best, bestpos = 0.0, pos
            for i in range(pos, max(pos + 1, len(b) - len(uw) + 2)):
                r = difflib.SequenceMatcher(None, uw, b[i:i + len(uw)], autojunk=False).ratio()
                if r > best:
                    best, bestpos = r, i
            if best < 0.7:
                missing.append((u, round(best, 2)))
            else:
                pos = bestpos + max(1, len(uw) // 2)
        ok = ratio >= min_ratio and abs(lenr - 1) <= max_len_dev and not missing
        return ok, ratio, lenr, missing


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def curl(args):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("OPENAI_API_KEY is not set. Load it into this command's environment (see the skill, section 1).")
    r = subprocess.run(["curl", "-sS", "--fail-with-body", "-H", "@-"] + args,
                       input=f"Authorization: Bearer {key}\n".encode(), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl exit {r.returncode}: {r.stdout[:400]!r} {r.stderr[:400]!r}")
    return r.stdout


def transcribe(path):
    return json.loads(curl(["https://api.openai.com/v1/audio/transcriptions",
                            "-F", f"file=@{path}", "-F", "model=whisper-1",
                            "-F", "response_format=verbose_json",
                            "-F", "timestamp_granularities[]=segment"]))


def duration(path, stream=None):
    sel = ["-select_streams", stream, "-show_entries", "stream=duration"] if stream \
        else ["-show_entries", "format=duration"]
    return float(subprocess.check_output(["ffprobe", "-v", "error", *sel, "-of", "csv=p=0", path]).decode().strip())


def silences(path, d, noise="-45dB"):
    log = run(["ffmpeg", "-i", path, "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"]).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def frame_count(path):
    return int(subprocess.check_output(
        ["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v",
         "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path]).strip())


def scene_classes(b):
    """[(ClassName, sid)] in file order."""
    src = open(b.p("scenes.py")).read()
    return re.findall(r'class (\w+)\(Base\):\s*\n\s*sid = "([^"]+)"', src)


# ---------------------------------------------------------------- commands

def cmd_init(b):
    os.makedirs(b.p("clips"), exist_ok=True)
    for f in ("base.py", "manim.cfg"):
        shutil.copy(os.path.join(HERE, f), b.p(f))
    print(f"build dir ready: {b.dir}")


def trim(b, sid):
    """Edge silence -> 30 ms, inner pauses > 0.4 s -> 0.4 s.

    Edge silence shifts the voice off its timeline slot; TTS pauses of
    0.7-1.1 s between sentences read as dropouts. silenceremove does not
    shorten inner pauses reliably, so cut PCM samples directly.
    """
    clean = b.clip(sid) + ".pcm.wav"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", b.clip(sid), "-c:a", "pcm_s16le", clean])
    with wave.open(clean) as w:
        params, rate = w.getparams(), w.getframerate()
        data = w.readframes(w.getnframes())
    total = len(data) / (params.sampwidth * params.nchannels) / rate
    cuts = []
    for a, e in silences(clean, 0.05):
        e = total if e is None else e
        if a <= 0.01:
            cuts.append((0.0, max(0.0, e - 0.03)))
        elif e >= total - 0.01:
            cuts.append((a + 0.03, total))
        elif e - a > 0.4:
            cuts.append((a + 0.2, e - 0.2))
    bpf = params.sampwidth * params.nchannels
    keep, pos = [], 0.0
    for a, e in cuts:
        keep.append(data[int(pos * rate) * bpf:int(a * rate) * bpf])
        pos = e
    keep.append(data[int(pos * rate) * bpf:])
    with wave.open(b.clip(sid, trimmed=True), "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(keep))
    os.remove(clean)
    left = [s for s in silences(b.clip(sid, True), 0.7) if s[0] > 0.01 and s[1] is not None]
    if left:
        sys.exit(f"FAIL: {sid} still has pauses >= 0.7 s after trimming: {left}")


def cmd_clips(b):
    os.makedirs(b.p("clips"), exist_ok=True)
    cache_p = b.p("clips", "hashes.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    for sc in b.script():
        text = b.apply_pron(sc["narration"])
        h = hashlib.sha256(json.dumps([text, TTS], sort_keys=True).encode()).hexdigest()
        out = b.clip(sc["id"])
        if os.path.exists(out) and cache.get(sc["id"]) == h:
            if not os.path.exists(b.clip(sc["id"], True)):
                trim(b, sc["id"])
            print(f"{sc['id']}: cached")
            continue
        for attempt in range(1, 4):
            req = b.p("clips", f"{sc['id']}.req.json")
            json.dump({**TTS, "input": text}, open(req, "w"))
            curl(["https://api.openai.com/v1/audio/speech", "-H", "Content-Type: application/json",
                  "--data-binary", f"@{req}", "-o", out])
            os.remove(req)
            tr = transcribe(out)["text"]
            ok, ratio, lenr, missing = b.match(sc["narration"], tr, 0.9, 0.07)
            print(f"{sc['id']}: try {attempt} similarity={ratio:.3f} length={lenr:.3f} "
                  f"dur={duration(out):.2f}s missing={missing}")
            if ok:
                trim(b, sc["id"])
                cache[sc["id"]] = h
                json.dump(cache, open(cache_p, "w"), indent=1)
                break
            print(f"   heard: {tr}")
        else:
            sys.exit(f"FAIL: clip {sc['id']} did not pass after 3 tries. If the 'missing' text "
                     f"was misheard, not dropped, add the spelling to pronunciations.json 'reverse'.")


def cmd_timeline(b):
    t, scenes = 0.0, []
    for sc in b.script():
        cd = duration(b.clip(sc["id"], trimmed=True))
        d = math.ceil((LEAD_IN + cd + TAIL) * FPS - 1e-9) / FPS
        scenes.append({"id": sc["id"], "start": round(t, 6), "duration": d,
                       "clip_start": round(t + LEAD_IN, 6), "clip_duration": cd,
                       "narration": sc["narration"]})
        t = round(t + d, 6)
    json.dump({"fps": FPS, "lead_in": LEAD_IN, "tail": TAIL, "total": t, "scenes": scenes},
              open(b.p("timeline.json"), "w"), indent=1)
    words = sum(len(s["narration"].split()) for s in scenes)
    print(f"total {int(t // 60)}:{t % 60:05.2f}, {words} words, {len(scenes)} scenes")
    if not 285 <= t <= 390:
        print("WARNING: total is outside 4:45-6:30; adjust the script before rendering.")


def cmd_lint(b):
    tl = {s["id"]: s["narration"] for s in b.timeline()["scenes"]}
    order = [s["id"] for s in b.timeline()["scenes"]]
    src = open(b.p("scenes.py")).read()
    pairs = scene_classes(b)
    errs = []
    if [sid for _, sid in pairs] != order:
        errs.append(f"scene classes {[s for _, s in pairs]} do not match timeline order {order}")
    blocks = re.split(r"\nclass ", src)
    for blk in blocks:
        m = re.search(r'sid = "([^"]+)"', blk)
        if not m or m.group(1) not in tl:
            continue
        narr, last = tl[m.group(1)], -1
        for ph in re.findall(r'self\.at\("([^"]+)"', blk):
            i = narr.find(ph)
            if i < 0:
                errs.append(f"{m.group(1)}: cue not in narration: {ph!r}")
            elif i < last:
                errs.append(f"{m.group(1)}: cue out of order: {ph!r}")
            last = max(last, i)
    print("\n".join(errs) if errs else "lint ok")
    sys.exit(1 if errs else 0)


def cmd_render(b, preview):
    pairs = scene_classes(b)
    q = ["-ql"] if preview else ["-qh", "--fps", "60", "-r", "1920,1080"]
    sub = "480p15" if preview else "1080p60"
    vdir = b.p("media", "videos", "scenes", sub)
    procs = []
    for name, _ in pairs:
        log = open(b.p(f"render_{name}.log"), "w")
        procs.append((name, log, subprocess.Popen(
            ["manim", *q, "--media_dir", b.p("media"), "-o", f"{name}.mp4", "scenes.py", name],
            cwd=b.dir, stdout=log, stderr=subprocess.STDOUT)))
        while sum(p.poll() is None for _, _, p in procs) >= 4:
            time.sleep(0.5)
    failed = []
    for name, log, p in procs:
        if p.wait() != 0:
            failed.append(name)
        log.close()
    if failed:
        for n in failed:
            print(f"--- {n} ---\n" + "".join(open(b.p(f"render_{n}.log")).readlines()[-20:]))
        sys.exit(f"FAIL: render failed for {failed}")
    if preview:
        os.makedirs(b.p("preview"), exist_ok=True)
        for i, (name, _) in enumerate(pairs):
            f = os.path.join(vdir, f"{name}.mp4")
            subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, duration(f) - 0.9)}",
                                   "-i", f, "-frames:v", "1", b.p("preview", f"{i:02d}.png")])
        cols = 3
        rows = math.ceil(len(pairs) / cols)
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", b.p("preview", "%02d.png"),
                               "-vf", f"tile={cols}x{rows}:padding=4", "-frames:v", "1",
                               b.p("preview", "sheet.png")])
        print(f"contact sheet: {b.p('preview', 'sheet.png')}")
        return
    tl = {s["id"]: s for s in b.timeline()["scenes"]}
    bad = []
    for name, sid in pairs:
        n, want = frame_count(os.path.join(vdir, f"{name}.mp4")), round(tl[sid]["duration"] * FPS)
        if n != want:
            bad.append(f"{name}: {n} frames, timeline wants {want}")
    if bad:
        sys.exit("FAIL: frame counts differ from timeline:\n" + "\n".join(bad))
    print(f"rendered {len(pairs)} scenes, frame counts match the timeline")


def cmd_assemble(b, out):
    pairs = scene_classes(b)
    vdir = b.p("media", "videos", "scenes", "1080p60")
    with open(b.p("concat.txt"), "w") as f:
        for name, _ in pairs:
            f.write(f"file '{os.path.join(vdir, name + '.mp4')}'\n")
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                           "-i", b.p("concat.txt"), "-c", "copy", b.p("video.mp4")])
    vd = duration(b.p("video.mp4"), "v")
    tl = b.timeline()["scenes"]
    args = ["ffmpeg", "-v", "error", "-y"]
    for s in tl:
        args += ["-i", b.clip(s["id"], trimmed=True)]
    parts = [f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,adelay={round(s['clip_start'] * 1000)}:all=1[a{i}]"
             for i, s in enumerate(tl)]
    parts.append("".join(f"[a{i}]" for i in range(len(tl)))
                 + f"amix=inputs={len(tl)}:normalize=0:duration=longest,apad[out]")
    subprocess.check_call(args + ["-filter_complex", ";".join(parts), "-map", "[out]", "-t", f"{vd}",
                                  "-ar", "48000", "-c:a", "pcm_s16le", b.p("narration.wav")])
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", b.p("video.mp4"), "-i", b.p("narration.wav"),
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-t", f"{vd}", "-movflags", "+faststart", out])
    print(f"wrote {out} ({vd:.3f}s)")


def cmd_qa(b, out):
    tl = b.timeline()
    res = []

    def probe(*a):
        return subprocess.check_output(["ffprobe", "-v", "error", *a, out]).decode().strip()

    # 1. durations
    vd, ad = duration(out, "v"), duration(out, "a")
    res.append(("1 durations match", f"video {vd:.4f}s, audio {ad:.4f}s, diff {abs(vd - ad) * 1000:.1f} ms",
                abs(vd - ad) <= 1 / 60 + 1e-6))

    # 2. transcript of the final audio track (stream copy, no re-encode)
    m4a = b.p("final_audio.m4a")
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", out, "-vn", "-c:a", "copy", m4a])
    tr = transcribe(m4a)
    json.dump(tr, open(b.p("final_transcript.json"), "w"), indent=1)
    full = " ".join(s["narration"] for s in tl["scenes"])
    ok, ratio, lenr, missing = b.match(full, tr["text"], 0.93, 0.04)
    res.append(("2 transcript complete", f"similarity {ratio:.3f}, length ratio {lenr:.3f}, "
                f"missing {len(missing)}" + (f" {missing}" if missing else ""), ok))

    # 3. sync. Whisper timestamps cannot resolve +-0.3 s (segments absorb the
    # preceding silence, words drift up to ~2 s), so measure the voice onset
    # from the audio: the silence end between the previous clip and this one.
    ends = [e for _, e in silences(out, 0.3) if e is not None]
    worst, det, ok3, prev = 0.0, [], True, 0.0
    for s in tl["scenes"]:
        cs = s["clip_start"]
        win = [e for e in ends if prev - 0.05 <= e <= cs + 1.0]
        if not win:
            det.append(f"{s['id']}:no-onset")
            ok3 = False
        else:
            d = min(win, key=lambda e: abs(e - cs)) - cs
            det.append(f"{s['id']}:{d:+.2f}")
            worst = max(worst, abs(d))
            ok3 = ok3 and abs(d) <= 0.3
        prev = cs + s["clip_duration"]
    res.append(("3 in sync (±0.3 s)", f"worst {worst:.2f}s; " + " ".join(det), ok3))

    # 4. dropouts
    gap_max = tl["tail"] + tl["lead_in"] + 0.2
    sil = [(a, vd if e is None else e) for a, e in silences(out, 0.7)]
    bad = []
    for a, e in sil:
        for s in tl["scenes"]:
            if s["clip_start"] + 0.05 < a < s["clip_start"] + s["clip_duration"] - 0.7:
                bad.append(f"{a:.2f}-{e:.2f} inside {s['id']}")
        if e - a > gap_max and a < vd - 1.5:
            bad.append(f"gap {a:.2f}-{e:.2f} = {e - a:.2f}s > {gap_max:.2f}s")
    res.append(("4 no dropouts", "; ".join(bad) if bad else f"{len(sil)} silences ≥0.7 s, all between clips",
                not bad))

    # 5. format
    v = json.loads(probe("-select_streams", "v", "-show_entries", "stream=codec_name,width,height,r_frame_rate",
                         "-of", "json"))["streams"][0]
    a = json.loads(probe("-select_streams", "a", "-show_entries", "stream=codec_name,sample_rate",
                         "-of", "json"))["streams"][0]
    fd = float(probe("-show_entries", "format=duration", "-of", "csv=p=0"))
    ok5 = (v["width"], v["height"]) == (1920, 1080) and v["r_frame_rate"] == "60/1" \
        and v["codec_name"] == "h264" and a["codec_name"] == "aac" and 285 <= fd <= 390
    res.append(("5 format", f"{v['width']}x{v['height']} {v['r_frame_rate']} {v['codec_name']} + "
                f"{a['codec_name']} {a['sample_rate']} Hz, {int(fd // 60)}:{fd % 60:05.2f}", ok5))

    print("| Check | Measured | Result |\n|---|---|---|")
    for n, val, ok in res:
        print(f"| {n} | {val} | {'PASS' if ok else 'FAIL'} |")
    sys.exit(0 if all(r[2] for r in res) else 1)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, b = sys.argv[1], Build(sys.argv[2])
    rest = sys.argv[3:]
    if cmd == "init":
        cmd_init(b)
    elif cmd == "clips":
        cmd_clips(b)
    elif cmd == "timeline":
        cmd_timeline(b)
    elif cmd == "lint":
        cmd_lint(b)
    elif cmd == "render":
        cmd_render(b, "--preview" in rest)
    elif cmd == "assemble":
        cmd_assemble(b, rest[0])
    elif cmd == "qa":
        cmd_qa(b, rest[0])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

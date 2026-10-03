"""Shared scene base for /devkit:video. `vidkit.py init` copies this file into
the build dir; scenes.py does `from base import *`.

Each scene subclasses Base, sets `sid` to its script.json id, and uses:
    self.at("phrase")   wait until the narration reaches that phrase
    self.p(*anims, rt)  play for rt seconds (rounded to whole frames)
    self.w(sec)         wait
    self.finish()       fade out inside the tail, pad to the exact duration
"""
import json
import os

from manim import *

_B = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(_B, "timeline.json")))
FPS = TL["fps"]

BG = "#0d1117"
BLUE = "#58C4DD"
YELLOW = "#F7D96F"
TEAL = "#5CD0B3"
RED = "#FC6255"
GREEN = "#83C167"
GREY = "#6b7280"
FG = "#e6edf3"
MONO = "Menlo"
SANS = "Helvetica Neue"

Text.set_default(font=SANS, color=FG)


def T(s, size=36, color=FG, **kw):
    """Sans text."""
    return Text(s, font=SANS, font_size=size, color=color, **kw)


def C(s, size=30, color=FG, **kw):
    """One line of monospace text. For more than one line of code, use code()."""
    return Text(s, font=MONO, font_size=size, color=color, **kw)


def code(src, language="go", size=24):
    """Syntax-highlighted code block. Highlight a line via .code_lines[i]."""
    return Code(code_string=src, language=language, formatter_style="monokai",
                add_line_numbers=False, background="rectangle",
                background_config={"fill_color": "#161b22", "stroke_color": GREY, "stroke_width": 1},
                paragraph_config={"font": MONO, "font_size": size})


def chip(s, color=YELLOW, size=26):
    """Rounded label, e.g. an assumption or a tag."""
    t = T(s, size=size, color=color)
    r = RoundedRectangle(corner_radius=0.15, width=t.width + 0.4, height=t.height + 0.3,
                         stroke_color=color, stroke_width=2, fill_color=tint(color), fill_opacity=1)
    return VGroup(r, t.move_to(r))


def tint(color, amount=0.12):
    """Opaque mix of color into the background: looks like a 12 % fill but hides
    lines behind it (Graph edges run centre to centre)."""
    return interpolate_color(ManimColor(BG), ManimColor(color), amount)


def box(label, color=BLUE, w=2.6, h=1.0, size=28, mono=False):
    """Labelled component box (opaque fill, z_index 1). Text shrinks to fit."""
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h, stroke_color=color,
                         stroke_width=3, fill_color=tint(color), fill_opacity=1)
    t = (C if mono else T)(label, size=size, color=FG)
    if t.width > w - 0.3:
        t.scale_to_fit_width(w - 0.3)
    return VGroup(r, t.move_to(r)).set_z_index(1)


def tree(vertices, edges, root, mobs, scale=(3.2, 2.4)):
    """Top-down tree via Graph(layout="tree"). Children keep the order of
    `edges` (Graph's tree layout reverses it, so feed it reversed)."""
    order = list(reversed(edges))
    return Graph(vertices, order, vertex_mobjects=mobs, layout="tree", root_vertex=root,
                 layout_scale=scale, edge_config={"stroke_color": GREY, "stroke_width": 2})


def fit(m, margin=0.8):
    """Scale m down (never up) to fit inside the frame."""
    if m.width > config.frame_width - margin:
        m.scale_to_fit_width(config.frame_width - margin)
    if m.height > config.frame_height - margin:
        m.scale_to_fit_height(config.frame_height - margin)
    return m


class Base(Scene):
    sid = None

    def setup(self):
        s = next(x for x in TL["scenes"] if x["id"] == self.sid)
        self.frames_total = round(s["duration"] * FPS)
        self.cd = s["clip_duration"]
        self.narr = s["narration"]
        self.f = 0
        self.camera.background_color = BG

    def cue(self, phrase, off=0.0):
        """Estimated time of `phrase`, from its position in the narration."""
        return TL["lead_in"] + self.cd * self.narr.index(phrase) / len(self.narr) + off

    def p(self, *anims, rt=1.0, **kw):
        n = max(1, round(rt * FPS))
        # play() renders len(arange(0, run_time, 1/FPS)) frames: (n - 0.5)/FPS gives exactly n.
        self.play(*anims, run_time=(n - 0.5) / FPS, **kw)
        self.f += n

    def w(self, sec):
        n = round(sec * FPS)
        if n > 0:
            # frozen waits render int(duration * FPS) frames: +0.5 survives float truncation.
            self.wait((n + 0.5) / FPS, frozen_frame=True)
            self.f += n

    def at(self, phrase, off=0.0):
        self.w(self.cue(phrase, off) - self.f / FPS)

    def finish(self):
        self.w((self.frames_total - round(0.5 * FPS) - self.f) / FPS)
        if self.mobjects:
            self.p(*[FadeOut(m) for m in self.mobjects], rt=0.4)
        remaining = self.frames_total - self.f
        assert remaining >= 0, f"{self.sid}: animations overran the scene by {-remaining} frames; shorten run times"
        self.w(remaining / FPS)

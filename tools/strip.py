"""Lay rendered frames of one task out as a row of captioned cards.

Every frame of a strip shares one camera, so all frames get the same crop: the union of
what differs from the background, padded. Each card gets a title, a checks-passed badge
and a one-line note.

Usage: python tools/strip.py spec.json
spec: {"out": "docs/images/x.png",
       "frames": [{"png": "...", "title": "Step 100", "passed": 7, "checks": 9, "note": "..."}]}
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CARD_W, IMG_H, CAP_H, GAP, PAD = 600, 420, 184, 24, 28
INK, MUTED, CARD = (31, 35, 40), (89, 99, 110), (255, 255, 255)
DOTS = {"fail": (207, 34, 46), "part": (191, 135, 0), "pass": (26, 127, 55)}
FONT_DIRS = ["/usr/share/fonts/noto", "/usr/share/fonts/truetype/noto", "/System/Library/Fonts/Supplemental"]


def font(name, size):
    for d in FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size)


def content_box(images, thresh=18, pad=0.08, aspect=CARD_W / IMG_H):
    """Bounding box of non-background pixels across all frames, padded to the card's aspect."""
    mask = None
    for im in images:
        a = np.asarray(im.convert("RGB")).astype(int)
        bg = np.median(np.concatenate([a[:8, :8], a[:8, -8:], a[-8:, :8], a[-8:, -8:]]).reshape(-1, 3), axis=0)
        m = np.abs(a - bg).max(axis=2) > thresh
        mask = m if mask is None else mask | m
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = (x1 - x0) * (1 + 2 * pad), (y1 - y0) * (1 + 2 * pad)
    w, h = max(w, h * aspect), max(h, w / aspect)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    W, H = images[0].size
    w, h = min(w, W, H * aspect), min(h, H, W / aspect)
    left, top = min(max(cx - w / 2, 0), W - w), min(max(cy - h / 2, 0), H - h)
    return tuple(int(round(v)) for v in (left, top, left + w, top + h))


def wrap(draw, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def card(im, fr, fonts):
    title_f, note_f, badge_f = fonts
    c = Image.new("RGB", (CARD_W, IMG_H + CAP_H), CARD)
    c.paste(im.resize((CARD_W, IMG_H), Image.LANCZOS), (0, 0))
    d = ImageDraw.Draw(c)
    y = IMG_H + 22
    d.text((PAD, y), fr["title"], font=title_f, fill=INK)
    score = f"{fr['passed']} / {fr['checks']}"
    state = "pass" if fr["passed"] == fr["checks"] else "fail" if fr["passed"] == 0 else "part"
    tw = d.textlength(score, font=badge_f)
    bx1 = CARD_W - PAD
    bx0 = bx1 - tw - 58
    d.rounded_rectangle((bx0, y + 2, bx1, y + 46), radius=22, outline=(208, 215, 222), width=2)
    d.ellipse((bx0 + 18, y + 17, bx0 + 32, y + 31), fill=DOTS[state])
    d.text((bx0 + 42, y + 5), score, font=badge_f, fill=INK)
    for i, line in enumerate(wrap(d, fr["note"], note_f, CARD_W - 2 * PAD)[:2]):
        d.text((PAD, y + 62 + i * 38), line, font=note_f, fill=MUTED)
    mask = Image.new("L", c.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, c.width - 1, c.height - 1), radius=22, fill=255)
    return c, mask


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    frames = spec["frames"]
    images = [Image.open(fr["png"]).convert("RGB") for fr in frames]
    box = content_box(images)
    fonts = (font("NotoSans-Bold.ttf", 38), font("NotoSans-Regular.ttf", 30), font("NotoSans-Medium.ttf", 30))
    n = len(frames)
    out = Image.new("RGBA", (n * CARD_W + (n - 1) * GAP, IMG_H + CAP_H), (0, 0, 0, 0))
    for i, (im, fr) in enumerate(zip(images, frames)):
        c, mask = card(im.crop(box), fr, fonts)
        out.paste(c, (i * (CARD_W + GAP), 0), mask)
    out.save(spec["out"], optimize=True)
    print("wrote", spec["out"], out.size, "crop", box)


if __name__ == "__main__":
    main(sys.argv[1])

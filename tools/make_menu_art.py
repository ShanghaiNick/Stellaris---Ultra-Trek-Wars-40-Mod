"""Draw the Starhammer main-menu logo and background. Original procedural art: no franchise imagery.

    python tools/make_menu_art.py            writes the two .dds files into mod/gfx/interface/main/
    python tools/make_menu_art.py --preview  also writes PNG previews into docs/

Needs Pillow and numpy.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mod" / "gfx" / "interface" / "main"
W, H = 2560, 1440
SEED = 4040


def fbm(rng: np.random.Generator, w: int, h: int, octaves: int = 6, base: int = 4) -> np.ndarray:
    """Smooth cloud noise in 0..1: random grids of rising detail, blown up and summed."""
    total = np.zeros((h, w), dtype=np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        n = base * (2 ** o)
        grid = (rng.random((max(2, n * h // w), n)) * 255).astype(np.uint8)
        layer = np.asarray(Image.fromarray(grid).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0
        total += layer * amp
        norm += amp
        amp *= 0.55
    total /= norm
    lo, hi = np.percentile(total, 2), np.percentile(total, 98)
    return np.clip((total - lo) / (hi - lo), 0, 1)


def background() -> Image.Image:
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img = np.zeros((H, W, 3), dtype=np.float32)

    # deep-space base, a little lighter toward the lower right where the world sits
    d = np.clip(1 - np.hypot(xx - W * 0.78, yy - H * 0.86) / (W * 0.9), 0, 1)
    img += np.stack([0.010 + 0.03 * d, 0.014 + 0.04 * d, 0.030 + 0.07 * d], axis=-1)

    # two nebulae: steel blue on the left, forge orange across the right
    band = np.exp(-((yy - (H * 0.50 + (xx - W / 2) * 0.22)) / (H * 0.36)) ** 2)
    n1, n2, n3 = fbm(rng, W, H), fbm(rng, W, H, base=3), fbm(rng, W, H, octaves=7, base=6)
    blue = np.clip(n1 - 0.34, 0, 1) ** 1.5 * band * np.clip(1.25 - xx / (W * 0.62), 0, 1)
    orange = np.clip(n2 - 0.36, 0, 1) ** 1.5 * band * np.clip((xx - W * 0.30) / (W * 0.55), 0, 1)
    dust = 0.35 + 0.65 * n3
    img += blue[..., None] * dust[..., None] * np.array([0.16, 0.42, 0.78]) * 5.5
    img += orange[..., None] * dust[..., None] * np.array([0.95, 0.42, 0.12]) * 5.0

    # stars: many faint, few bright, kept out of the menu column's text only by being small
    stars = np.zeros((H, W), dtype=np.float32)
    n = 5200
    sx, sy = rng.integers(0, W, n), rng.integers(0, H, n)
    stars[sy, sx] = rng.random(n) ** 6 * 1.4 + 0.08
    soft = np.asarray(Image.fromarray((np.clip(stars, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)),
                      dtype=np.float32) / 255.0
    tint = 0.85 + 0.15 * fbm(rng, W, H, octaves=2, base=8)
    img += (stars + soft * 2.2)[..., None] * np.stack([tint, tint * 0.97, np.ones_like(tint)], axis=-1)

    # a dark world on the lower right with a thin lit rim
    cx, cy, r = W * 0.86, H * 1.18, H * 0.74
    dist = np.hypot(xx - cx, yy - cy)
    inside = dist < r
    limb = np.exp(-np.abs(dist - r) / 5.0) * np.clip((cx - xx) / r + 0.55, 0, 1)
    glow = np.exp(-np.clip(dist - r, 0, None) / 46.0) * (dist >= r) * np.clip((cx - xx) / r + 0.6, 0, 1)
    surface = fbm(rng, W, H, octaves=5, base=10)
    shade = np.clip((r - dist) / r, 0, 1)
    img[inside] = (np.array([0.020, 0.026, 0.040]) * (0.6 + 0.8 * surface[inside, None])
                   + np.array([0.10, 0.07, 0.05]) * np.clip(0.10 - shade[inside, None], 0, 1) * 6)
    img += limb[..., None] * np.array([1.0, 0.72, 0.45]) * 0.95 + glow[..., None] * np.array([0.55, 0.30, 0.16]) * 0.35

    # darken the left third so the menu text stays readable, then a gentle vignette
    img *= (0.50 + 0.50 * np.clip((xx - W * 0.04) / (W * 0.30), 0, 1))[..., None]
    v = 1 - 0.38 * (np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)) / 1.4142) ** 2.2
    img = np.clip(img * v[..., None], 0, 1) ** (1 / 1.12)
    return Image.fromarray((img * 255).astype(np.uint8), "RGB")


def emblem(size: int) -> Image.Image:
    """A four-point star with a hammer laid across it."""
    s = size * 4
    im = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(im)
    c = s / 2
    pts = []
    for i in range(8):
        a = math.pi / 2 * (i / 2) - math.pi / 2
        rad = s * (0.48 if i % 2 == 0 else 0.085)
        pts.append((c + rad * math.cos(a), c + rad * math.sin(a)))
    d.polygon(pts, fill=255)
    ham = Image.new("L", (s, s), 0)
    hd = ImageDraw.Draw(ham)
    hd.rectangle([c - s * 0.035, c - s * 0.30, c + s * 0.035, c + s * 0.34], fill=255)       # haft
    hd.rectangle([c - s * 0.20, c - s * 0.36, c + s * 0.20, c - s * 0.20], fill=255)         # head
    ham = ham.rotate(-38, resample=Image.BICUBIC, center=(c, c))
    cut = ham.filter(ImageFilter.MaxFilter(int(s * 0.03) | 1))                                # gap around the hammer
    star = ImageChops.subtract(im, cut)
    return ImageChops.lighter(star, ham).resize((size, size), Image.LANCZOS)


def logo() -> Image.Image:
    lw, lh = 900, 170
    scale = 3
    big = Image.new("L", (lw * scale, lh * scale), 0)
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype(r"C:\Windows\Fonts\bahnschrift.ttf", 62 * scale)
    try:
        font.set_variation_by_axes([420, 100])      # light weight, normal width
    except Exception:
        pass
    text, x, track = "STARHAMMER", 148 * scale, 17 * scale
    for ch in text:
        d.text((x, 52 * scale), ch, font=font, fill=255)
        x += d.textlength(ch, font=font) + track
    em = emblem(86 * scale)
    big.paste(em, (52 * scale, 42 * scale), em)
    mask = big.resize((lw, lh), Image.LANCZOS)
    glow = mask.filter(ImageFilter.GaussianBlur(6))
    alpha = ImageChops.lighter(mask, glow.point(lambda p: int(p * 0.45)))
    out = Image.new("RGBA", (lw, lh), (236, 240, 245, 0))
    out.putalpha(alpha)
    return out


SISYPHUS_SRC = Path(r"C:\Users\Nicho\Sisyphus\Webpage\images\sisyphus_ai_logo_1000.jpg")


def sisyphus_mark(width: int = 300) -> Image.Image:
    """The Sisyphus AI emblem and wordmark, lifted off its dark plate: brightness becomes transparency."""
    crop = Image.open(SISYPHUS_SRC).convert("RGB").crop((140, 150, 890, 770))
    a = np.asarray(crop, dtype=np.float32)
    alpha = np.clip((a.max(axis=2) - 48) / 70.0, 0, 1)
    rgb = np.clip(a * 1.25 + 20, 0, 255)
    out = Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")
    return out.resize((width, round(crop.height * width / crop.width)), Image.LANCZOS)


KEYART = ROOT / "art" / "menu_keyart.png"


def keyart_background() -> Image.Image:
    """Fit art/menu_keyart.png to the menu: scale to cover 2560x1440, centre-crop, darken the menu column a little."""
    src = Image.open(KEYART).convert("RGB")
    k = max(W / src.width, H / src.height)
    big = src.resize((round(src.width * k), round(src.height * k)), Image.LANCZOS)
    x0, y0 = (big.width - W) // 2, (big.height - H) // 2
    a = np.asarray(big.crop((x0, y0, x0 + W, y0 + H)), dtype=np.float32) / 255.0
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    a *= 0.70 + 0.30 * np.clip((xx - W * 0.02) / (W * 0.22), 0, 1)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    lg = logo()
    if KEYART.exists():                # a painted picture wins over the procedural nebula
        bg = keyart_background()
    else:
        bg = background()
    bg.save(OUT / "starhammer_menu_bg.dds", pixel_format="DXT1")
    lg.save(OUT / "game_logo.dds")
    mark = None
    if SISYPHUS_SRC.exists():          # the source logo lives outside this repository; skip if absent
        mark = sisyphus_mark()
        mark.save(OUT / "sisyphus_logo.dds")
    print("wrote", OUT / "starhammer_menu_bg.dds", bg.size, "and", OUT / "game_logo.dds", lg.size)
    if "--preview" in sys.argv:
        (ROOT / "docs").mkdir(exist_ok=True)
        prev = bg.copy()
        prev.paste(lg, (50 - 53 + 53, 50 - 33 + 33), lg)
        if mark:
            prev.paste(mark, (W - 50 - mark.width, H - 50 - mark.height), mark)
        prev.resize((1280, 720), Image.LANCZOS).save(ROOT / "docs" / "menu_preview.png")
        print("wrote", ROOT / "docs" / "menu_preview.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

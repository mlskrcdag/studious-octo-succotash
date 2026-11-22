#!/usr/bin/env python3
"""TikTok foto-post üretici — "day in my life" estetiği.

Kullanım:
    python3 tiktok_post.py posts/ornek.json            # tek post
    python3 tiktok_post.py posts/*.json                # hepsi

Her JSON dosyası bir slaytı tarif eder (bkz. STYLE_GUIDE.md ve posts/ klasörü).
Çıktı: output/<json-adı>.jpg
"""
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# ---------------------------------------------------------------- paleti
PALETTE = {
    "cream": "#F6F1DE",      # büyük el yazısı başlık
    "white": "#FFFFFF",
    "blush": "#F2C6D3",      # "one", "6 am - 10 pm" gibi küçük etiketler
    "clock_bg": "#F2F2F2",   # flip-clock karoları
    "clock_ink": "#4A4A4A",  # flip-clock rakamları (nötr)
    "clock_pink": "#EC6F9A", # flip-clock rakamları (pembe varyant)
    "star_yellow": "#FFD34E",
}

FONT_FILES = {
    "script": "PinyonScript-Regular.ttf",   # "Day in my Life" başlığı
    "script2": "GreatVibes-Regular.ttf",    # "breakfast platter" yemek etiketi
    "script3": "Allura-Regular.ttf",
    "script4": "Parisienne-Regular.ttf",
    "sans": "Inter-Regular.otf",            # caption yazısı (iOS/TikTok sistem fontu hissi)
    "sans_light": "Inter-Light.otf",
    "sans_medium": "Inter-Medium.otf",      # flip-clock rakamları
}

_font_cache = {}


def font(name, size):
    key = (name, int(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS / FONT_FILES[name]), int(size))
    return _font_cache[key]


def color(c):
    return PALETTE.get(c, c)


def rgba(c, alpha=255):
    c = color(c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


# ---------------------------------------------------------------- emoji destekli metin
_EB = "[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2B55\u2300-\u23FF]"
_EM = "[\uFE0F\U0001F3FB-\U0001F3FF]*"
EMOJI_RE = re.compile("(" + _EB + _EM + "(?:\u200D" + _EB + _EM + ")*)")
_emoji_font = None


def _emoji_img(ch, px):
    global _emoji_font
    if _emoji_font is None:
        _emoji_font = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=_emoji_font, embedded_color=True)
    bbox = im.getbbox()
    if not bbox:
        return None
    im = im.crop(bbox)
    scale = px / 128
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def _runs(text):
    parts = EMOJI_RE.split(text)
    return [(p, i % 2 == 1) for i, p in enumerate(parts) if p]


def text_width(text, f):
    w = 0
    for chunk, is_emoji in _runs(text):
        w += f.size * 1.15 if is_emoji else f.getlength(chunk)
    return w


def draw_line(layer, xy, text, f, fill):
    x, y = xy
    d = ImageDraw.Draw(layer)
    ascent, _ = f.getmetrics()
    for chunk, is_emoji in _runs(text):
        if is_emoji:
            em = _emoji_img(chunk, f.size * 1.05)
            if em:
                layer.alpha_composite(em, (int(x), int(y + ascent - em.height * 0.88)))
            x += f.size * 1.15
        else:
            d.text((x, y), chunk, font=f, fill=fill)
            x += f.getlength(chunk)


def wrap(text, f, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if text_width(test, f) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- yerleşim (layout)
def fit(img, w, h, focus=(0.5, 0.5)):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=tuple(focus))


def load(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return ImageOps.exif_transpose(Image.open(p)).convert("RGB")


def build_base(spec):
    W, H = spec.get("size", [1080, 1440])
    layout = spec.get("layout", "full")
    photos = spec["photos"]
    foc = spec.get("focus", [[0.5, 0.5]] * len(photos))
    canvas = Image.new("RGB", (W, H), "white")
    split = spec.get("split", 0.5)
    if layout == "full":
        canvas.paste(fit(load(photos[0]), W, H, foc[0]), (0, 0))
    elif layout == "stack2":            # üst + alt (görsel 1, 3, 4)
        h1 = int(H * split)
        canvas.paste(fit(load(photos[0]), W, h1, foc[0]), (0, 0))
        canvas.paste(fit(load(photos[1]), W, H - h1, foc[1]), (0, h1))
    elif layout == "top_split":         # üstte tek, altta yan yana iki (görsel 2)
        h1 = int(H * split)
        canvas.paste(fit(load(photos[0]), W, h1, foc[0]), (0, 0))
        w2 = W // 2
        canvas.paste(fit(load(photos[1]), w2, H - h1, foc[1]), (0, h1))
        canvas.paste(fit(load(photos[2]), W - w2, H - h1, foc[2]), (w2, h1))
    else:
        raise ValueError(f"bilinmeyen layout: {layout}")
    return canvas.convert("RGBA")


# ---------------------------------------------------------------- öğeler
def shadowed(base, layer, blur, alpha):
    """Metnin altına yumuşak gölge — açık zeminlerde okunurluk için."""
    if alpha > 0:
        a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
        a = a.point(lambda v: int(v * alpha / 255))
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sh.putalpha(a)
        base.alpha_composite(sh)
    base.alpha_composite(layer)


def el_caption(base, e, W, H):
    """Beyaz, sade, ortalı caption (iOS Story yazısı hissi)."""
    f = font(e.get("font", "sans"), e.get("size", 0.03) * W)
    max_w = e.get("width", 0.62) * W
    lines = wrap(e["text"], f, max_w)
    lh = f.size * e.get("line_height", 1.22)
    block_h = lh * len(lines)
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    align = e.get("align", "center")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    for i, ln in enumerate(lines):
        tw = text_width(ln, f)
        if align == "left":
            x = cx
        elif align == "right":
            x = cx - tw
        else:
            x = cx - tw / 2
        draw_line(layer, (x, cy - block_h / 2 + i * lh), ln, f, rgba(e.get("color", "white")))
    shadowed(base, layer, f.size * 0.25, e.get("shadow", 90))


def el_script(base, e, W, H):
    """Büyük el yazısı başlık. Her satır ayrı konumlanabilir (merdiven efekti)."""
    f = font(e.get("font", "script"), e.get("size", 0.12) * W)
    lines = e["text"].split("\n")
    offsets = e.get("offsets", [0] * len(lines))   # satır başına yatay kayma (W oranı)
    lh = f.size * e.get("line_height", 0.95)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    top = cy - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        tw = f.getlength(ln)
        d.text((cx - tw / 2 + offsets[i] * W, top + i * lh), ln, font=f, fill=rgba(e.get("color", "cream")))
    if e.get("rotate"):
        layer = layer.rotate(e["rotate"], resample=Image.BICUBIC, center=(cx, cy))
    shadowed(base, layer, f.size * 0.06, e.get("shadow", 70))


def el_label(base, e, W, H):
    """Küçük ince sans etiket: 'one', '6 am - 10 pm'."""
    f = font(e.get("font", "sans_light"), e.get("size", 0.04) * W)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tw = text_width(e["text"], f)
    x = e.get("x", 0.5) * W
    if e.get("align", "left") == "center":
        x -= tw / 2
    draw_line(layer, (x, e.get("y", 0.1) * H), e["text"], f, rgba(e.get("color", "blush")))
    shadowed(base, layer, f.size * 0.2, e.get("shadow", 40))


def el_clock(base, e, W, H):
    """Flip-clock saat damgası: 4 açık gri karo, ortasında ince çizgi."""
    digits = e["time"].replace(":", "")
    tile_w = e.get("size", 0.065) * W
    tile_h = tile_w * 1.42
    gap = tile_w * 0.1
    total = tile_w * 4 + gap * 3
    x0 = e.get("x", 0.5) * W - total / 2
    y0 = e.get("y", 0.2) * H - tile_h / 2
    f = font("sans_medium", tile_h * 0.86)
    ink = rgba(e.get("color", "clock_ink"))
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, ch in enumerate(digits[:4]):
        x = x0 + i * (tile_w + gap)
        d.rounded_rectangle([x, y0, x + tile_w, y0 + tile_h], radius=tile_w * 0.12,
                            fill=rgba(e.get("bg", "clock_bg"), e.get("bg_alpha", 225)))
        bb = d.textbbox((0, 0), ch, font=f)
        d.text((x + (tile_w - (bb[2] - bb[0])) / 2 - bb[0],
                y0 + (tile_h - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=ink)
        my = y0 + tile_h / 2
        d.line([x, my, x + tile_w, my], fill=(120, 120, 120, 170), width=max(1, int(tile_h * 0.018)))
    shadowed(base, layer, tile_w * 0.15, e.get("shadow", 35))


def _star_points(cx, cy, r, rot=-90, inner=0.42):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + i * 36)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def el_star(base, e, W, H):
    """Yıldız sticker'ları: style = white | yellow | polka."""
    r = e.get("size", 0.025) * W
    cx, cy = e.get("x", 0.5) * W, e.get("y", 0.5) * H
    style = e.get("style", "white")
    rot = -90 + e.get("rotate", 0)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = _star_points(cx, cy, r, rot)
    if style == "yellow":
        d.polygon(_star_points(cx, cy, r, rot, 0.5), fill=rgba("star_yellow"))
        hl = _star_points(cx - r * 0.12, cy - r * 0.12, r * 0.45, rot, 0.5)
        d.polygon(hl, fill=(255, 240, 170, 200))
    elif style == "polka":
        d.polygon(pts, fill=rgba("#FBF6EA"))
        mask = Image.new("L", base.size, 0)
        ImageDraw.Draw(mask).polygon(pts, fill=255)
        dots = Image.new("RGBA", base.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(dots)
        step = r * 0.32
        yy = cy - r
        row = 0
        while yy < cy + r:
            xx = cx - r + (step / 2 if row % 2 else 0)
            while xx < cx + r:
                dd.ellipse([xx - step * 0.16, yy - step * 0.16, xx + step * 0.16, yy + step * 0.16], fill=(20, 20, 20, 255))
                xx += step
            yy += step * 0.9
            row += 1
        from PIL import ImageChops
        dots.putalpha(ImageChops.multiply(dots.getchannel("A"), mask))
        layer.alpha_composite(dots)
    else:
        d.polygon(pts, fill=rgba("white"))
    shadowed(base, layer, r * 0.12, e.get("shadow", 60))


def el_pill(base, e, W, H):
    """Konum/tarih hapı: yarı saydam beyaz zemin + pin ikonu + metin."""
    f = font("sans", e.get("size", 0.032) * W)
    text = e["text"]
    pad_x, pad_y = f.size * 0.75, f.size * 0.5
    icon_w = f.size * 0.9 if e.get("icon", True) else 0
    tw = text_width(text, f)
    w = tw + pad_x * 2 + icon_w
    h = f.size * 1.2 + pad_y * 2
    x0 = e.get("x", 0.5) * W - w / 2
    y0 = e.get("y", 0.9) * H - h / 2
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h * 0.32, fill=(255, 255, 255, e.get("alpha", 70)))
    ink = rgba(e.get("color", "white"))
    if icon_w:
        px, py, pr = x0 + pad_x + f.size * 0.3, y0 + h / 2 - f.size * 0.12, f.size * 0.3
        lw = max(2, int(f.size * 0.08))
        d.ellipse([px - pr, py - pr, px + pr, py + pr], outline=ink, width=lw)
        d.line([px - pr * 0.85, py + pr * 0.5, px, py + pr * 1.9], fill=ink, width=lw)
        d.line([px + pr * 0.85, py + pr * 0.5, px, py + pr * 1.9], fill=ink, width=lw)
        d.ellipse([px - pr * 0.3, py - pr * 0.3, px + pr * 0.3, py + pr * 0.3], outline=ink, width=lw)
    asc, desc = f.getmetrics()
    draw_line(layer, (x0 + pad_x + icon_w, y0 + (h - asc - desc) / 2), text, f, ink)
    base.alpha_composite(layer)


ELEMENTS = {
    "caption": el_caption, "script": el_script, "label": el_label,
    "clock": el_clock, "star": el_star, "pill": el_pill,
}


# ---------------------------------------------------------------- renk düzeltme (isteğe bağlı)
def grade(img, g):
    """Hafif 'warm & soft' ton: parlaklık, kontrast, sıcaklık, solukluk."""
    from PIL import ImageEnhance
    rgb = img.convert("RGB")
    rgb = ImageEnhance.Brightness(rgb).enhance(g.get("brightness", 1.0))
    rgb = ImageEnhance.Contrast(rgb).enhance(g.get("contrast", 1.0))
    rgb = ImageEnhance.Color(rgb).enhance(g.get("saturation", 1.0))
    warmth = g.get("warmth", 0)          # -20..20
    if warmth:
        r, gg, b = rgb.split()
        r = r.point(lambda v: min(255, v + warmth))
        b = b.point(lambda v: max(0, v - warmth))
        rgb = Image.merge("RGB", (r, gg, b))
    fade = g.get("fade", 0)              # 0..40: siyahları kaldırır (mat görünüm)
    if fade:
        rgb = rgb.point(lambda v: int(fade + v * (255 - fade) / 255))
    return rgb.convert("RGBA")


def render(spec_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    base = build_base(spec)
    if spec.get("grade"):
        base = grade(base, spec["grade"])
    W, H = base.size
    for e in spec.get("elements", []):
        ELEMENTS[e["type"]](base, e, W, H)
    out = ROOT / "output" / (Path(spec_path).stem + ".jpg")
    out.parent.mkdir(exist_ok=True)
    base.convert("RGB").save(out, quality=95)
    print("✓", out.relative_to(ROOT))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for p in sys.argv[1:]:
        render(p)
